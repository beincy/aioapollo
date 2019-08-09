import aiohttp
from enum import Enum
import threading
from datetime import datetime


class ConfigMode(Enum):
    """
     阿波罗配置拉取模式
    """
    PULL = 0  # 拉取模式，在使用的时候进行拉取，带缓存，可控制不带缓存。简单快速自由
    CHECKING = 1  # 定时检测模式，由系统进行不断的拉取配置


class ApolloConfig:
    """
    Apollo链接配置
    """
    configDir = {}
    serverUrl = None
    appId = None
    clusterName = None
    namespaceName = 'application'
    configMode = ConfigMode.PULL
    clientIp = ''
    periodTime = 0  # 失效时间

    def __init__(self,
                 configName,
                 serverUrl,
                 appId,
                 clusterName,
                 namespaceName='application',
                 configMode=ConfigMode.PULL,
                 clientIp='',
                 periodTime=3000):
        """
        configName：配置名称

        serverUrl:apollo的服务器的url 127.0.0.1:8080

        appId:应用的appId

        clusterName:集群名一般情况下传入 default 即可。 如果希望配置按集
            群划分，可以参考集群独立配置说明做相关配置，然后在这里填入对应的集群名。

        namespaceName:Namespace的名字如果没有新建过Namespace的话，传入application即可。 如果创
            建了Namespace，并且需要使用该Namespace的配置，则传入对应的Namespace名字。
            需要注意的是对于properties类型的namespace，只需要传入namespace的名字即可，如application。
            对于其它类型的namespace，需要传入namespace的名字加上后缀名，如datasources.json

        ip:应用部署的机器ip,这个参数是可选的，用来实现灰度发布。
            如果不想传这个参数，请注意URL中从?号开始的query parameters整个都不要出现。
        periodTime:缓存有效性，0代表即时有效
        """
        self.configDir[configName] = {
            "serverUrl": serverUrl,
            "appId": appId,
            "clusterName": clusterName,
            "namespaceName": namespaceName,
            "configMode": configMode,
            "periodTime": periodTime,
            "clientIp": clientIp,
        }

    @staticmethod
    def remoteUrl(configName):
        searchUrl = f'{ApolloConfig.configDir[configName]["serverUrl"]}/configfiles/json/{ApolloConfig.configDir[configName]["appId"]}/{ApolloConfig.configDir[configName]["clusterName"]}/{ApolloConfig.configDir[configName]["namespaceName"]}'
        if ApolloConfig.configDir[configName]["clientIp"]:
            searchUrl = f'{searchUrl}?ip={ApolloConfig.configDir[configName]["clientIp"]}'
        return searchUrl

    @staticmethod
    def remoteUrlNoCache(configName):
        searchUrl = f'{ApolloConfig.configDir[configName]["serverUrl"]}/configs/{ApolloConfig.configDir[configName]["appId"]}/{ApolloConfig.configDir[configName]["clusterName"]}/{ApolloConfig.configDir[configName]["namespaceName"]}'
        if ApolloConfig.configDir[configName]["clientIp"]:
            searchUrl = f'{searchUrl}?ip={ApolloConfig.configDir[configName]["clientIp"]}'
        return searchUrl

    @staticmethod
    def getPeriodTime(configName):
        return ApolloConfig.configDir[configName]["periodTime"]


class ApolloClient:
    """
    apollo配置服务基础类
    """
    mutex = threading.Lock()  # 锁一下
    _configCollection = {}  # 配置数据

    def __init__(self, configName=''):
        """
        配置名称
        """
        self._configName = configName
        if configName in self._configCollection:
            self._validConfig = self._configCollection[configName]['data']
            if (datetime.now()-self._configCollection[configName]['date']).seconds > ApolloConfig.getPeriodTime(configName):
                res = await self._getConfigRemote()
                if res:
                    self._configCollection.update({self._configName: res})
                    self._validConfig = res['data']
        else:
            res = await self._getConfigRemote()
            assert res is not None
            self._configCollection.update({self._configName: res})
            self._validConfig = self._configCollection[configName]['data']

    async def get(self, key, noCache=False):
        """
        根据key获取key对应的配置。
        """
        res = {}
        if noCache:
            res = await self._getConfigRemoteNoCache()
            if res:
                self._configCollection.update({self._configName: res})
                self._validConfig = res['data']
        return self._validConfig.get(key)

    async def _getConfigRemote(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(ApolloConfig.remoteUrl(
                    self._configName)) as resp:
                if resp.status == 200:
                    return {
                        "data": await resp.json(),
                        "date": datetime.now(),
                        "release": ""
                    }
        return None

    async def _getConfigRemoteNoCache(self):
        if self._validConfig:
            searchUrl = f'{ApolloConfig.remoteUrl( self._configName)}&releaseKey={self._validConfig["release"]}'
        async with aiohttp.ClientSession() as session:
            async with session.get(searchUrl) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    if res:
                        return {
                            "data": res.get('configurations'),
                            "date": datetime.now(),
                            "release": res.get('releaseKey')
                        }
        return None
