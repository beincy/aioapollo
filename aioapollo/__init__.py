import aiohttp
from enum import Enum
from threading import Thread
from datetime import datetime
import asyncio
import uvloop
from urllib.parse import quote
import ujson


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
                 periodTime=300):
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

        run_loop_thread = Thread(target=loopConfig)  # 将次事件循环运行在一个线程中，防止阻塞当前主线程
        run_loop_thread.start()  # 运行线程，同时协程事件循环也会运行

    @staticmethod
    def remoteUrl(configName):
        searchUrl = f'{ApolloConfig.configDir[configName]["serverUrl"]}/configfiles/json'
        searchUrl = f'{searchUrl}/{ApolloConfig.configDir[configName]["appId"]}'
        searchUrl = f'{searchUrl}/{ApolloConfig.configDir[configName]["clusterName"]}'
        searchUrl = f'{searchUrl}/{ApolloConfig.configDir[configName]["namespaceName"]}'
        if ApolloConfig.configDir[configName]["clientIp"]:
            searchUrl = f'{searchUrl}?ip={ApolloConfig.configDir[configName]["clientIp"]}'
        return searchUrl

    @staticmethod
    def remoteUrlNoCache(configName):
        searchUrl = f'{ApolloConfig.configDir[configName]["serverUrl"]}/configs'
        searchUrl = f'{searchUrl}/{ApolloConfig.configDir[configName]["appId"]}'
        searchUrl = f'{searchUrl}/{ApolloConfig.configDir[configName]["clusterName"]}'
        searchUrl = f'{searchUrl}/{ApolloConfig.configDir[configName]["namespaceName"]}'
        if ApolloConfig.configDir[configName]["clientIp"]:
            searchUrl = f'{searchUrl}?ip={ApolloConfig.configDir[configName]["clientIp"]}'
        return searchUrl

    @staticmethod
    def getPeriodTime(configName):
        return ApolloConfig.configDir[configName]["periodTime"]

    @staticmethod
    def startUp():
        for _, v in ApolloConfig.configDir.items():
            if v["configMode"] == ConfigMode.CHECKING:
                run_loop_thread = Thread(target=loopConfig)
                # 将次事件循环运行在一个线程中，防止阻塞当前主线程
                run_loop_thread.start()
                # 运行线程，同时协程事件循环也会运行
            break


class ApolloClient:
    """
    apollo配置服务基础类
    """
    _configCollection = {}  # 配置数据

    def __init__(self, configName=''):
        """
        配置名称
        """
        self._configName = configName

    async def get(self, key, noCache=False):
        """
        根据key获取key对应的配置。
        """
        res = {}
        if self._configName not in self._configCollection or \
                (datetime.now()-self._configCollection[self._configName]['date']).seconds >\
                ApolloConfig.getPeriodTime(self._configName):
            if noCache:
                res = await self._getConfigRemoteNoCache()
            else:
                res = await self._getConfigRemote()
            assert res is not None
            self._configCollection.update({self._configName: res})
        elif noCache:
            res = await self._getConfigRemoteNoCache()
            if res:
                self._configCollection.update({self._configName: res})
        return self._configCollection[self._configName].get('data').get(key)

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
        searchUrl = ApolloConfig.remoteUrlNoCache(self._configName)
        if self._configName in self._configCollection:
            searchUrl = f'{searchUrl}?releaseKey={self._configCollection[self._configName]["release"]}'
        else:
            searchUrl = f'{searchUrl}?releaseKey=-1'
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


def loopConfig():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(checkConfig())


async def checkConfig():
    configCyc = {}
    for configName, conItem in ApolloConfig.configDir.items():
        if conItem["configMode"] == ConfigMode.CHECKING:
            key = f'{conItem["serverUrl"]}:{conItem["appId"]}:{conItem["clusterName"]}'
            if key in configCyc:
                configCyc[key]["notifications"].append({
                    "namespaceName":
                    conItem["namespaceName"],
                    "notificationId":
                    0
                })
                configCyc[key][conItem["namespaceName"]] = {
                    "name": configName,
                    "data": conItem
                }
            else:
                configCyc[key] = {
                    "baseUrl":
                    f'{conItem["serverUrl"]}/notifications/v2?appId={conItem["appId"]}&cluster={conItem["clusterName"]}',
                    "notifications": [{
                        "namespaceName":
                        conItem["namespaceName"],
                        "notificationId":
                        0
                    }],
                    "configItems": {
                        conItem["namespaceName"]: {
                            "name": configName,
                            "data": conItem
                        }
                    }
                }
    tasks = []
    for _, configItem in configCyc.items():
        tasks.append(checkRemoteConfig(**configItem))
    await asyncio.gather(*tasks)


async def checkRemoteConfig(baseUrl, notifications, configItems):
    while True:
        searchUrl = f'{baseUrl}&notifications={quote(ujson.dumps(notifications))}'
        async with aiohttp.ClientSession() as session:
            async with session.get(searchUrl) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    if res:
                        for notification in res:
                            for eachnote in notifications:
                                if eachnote["namespaceName"] == notification[
                                        "namespaceName"]:
                                    eachnote["notificationId"] = notification[
                                        "notificationId"]
                            dataValue = configItems[
                                notification["namespaceName"]]["data"]
                            configRemoteUrl = f'{dataValue["serverUrl"]}/configs'
                            configRemoteUrl = f'{configRemoteUrl}/{dataValue["appId"]}'
                            configRemoteUrl = f'{configRemoteUrl}/{dataValue["clusterName"]}'
                            configRemoteUrl = f'{configRemoteUrl}/{dataValue["namespaceName"]}'
                            if dataValue["clientIp"]:
                                configRemoteUrl = f'{configRemoteUrl}?ip='
                                configRemoteUrl = f'{configRemoteUrl}{dataValue["clientIp"]}'
                            async with session.get(configRemoteUrl) as resp2:
                                if resp2.status == 200:
                                    res2 = await resp2.json()
                                    if res2:
                                        tempConfig = {
                                            "data": res2.get('configurations'),
                                            "date": datetime.now(),
                                            "release": res2.get('releaseKey')
                                        }
                                        ApolloClient._configCollection.update({
                                            configItems[notification["namespaceName"]]["name"]:
                                            tempConfig
                                        })
