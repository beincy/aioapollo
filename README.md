aioapollo

## 如何使用，how use it
### 初始化
> 你可以在程序的入口出对ApolloConfig进行初始化，以便于在代码中多次使用
```
 aioapollo.ApolloConfig("default", "http://192.168.88.103:8080", "SampleApp","default", "application", aioapollo.ConfigMode.PULL, periodTime=600)
```
> 当然你可以对多个节点进行初始化
```
 aioapollo.ApolloConfig("default", "http://192.168.88.103:8080", "SampleApp1","default", "application", aioapollo.ConfigMode.PULL, periodTime=600)
 aioapollo.ApolloConfig("default2", "http://192.168.88.103:8080", "SampleApp2","default", "application", aioapollo.ConfigMode.PULL, periodTime=600)
 aioapollo.ApolloConfig("default3", "http://192.168.88.103:8080", "SampleApp3","default", "application", aioapollo.ConfigMode.PULL, periodTime=600)
 aioapollo.ApolloConfig("default4", "http://192.168.88.103:8080", "SampleApp3","default", "application1", aioapollo.ConfigMode.PULL, periodTime=600)
```
> 组件支持两种模式，一种是主动拉取模式，另一种是检测变化模式。
> 《主动拉取模式》的使用
```
aioapollo.ApolloConfig("default", "http://192.168.88.103:8080", "SampleApp1","default", "application", aioapollo.ConfigMode.PULL, periodTime=600)
```
> 其中 aioapollo.ConfigMode.PULL 代表是拉取模式，periodTime 代表可接收超时时间（秒），如果系统中的配置一旦超过periodTime时间，在下次使用的之前会尝试拉取新的配置
> 例如：
```
apolloClient = aioapollo.ApolloClient("default")
text=await apolloClient.get("timeout")
```
# 但是如果在该配置下，有需要实时获取配置的需求怎么办。你可以在获取时候，指定强制刷新
```
apolloClient = aioapollo.ApolloClient("default")
text=await apolloClient.get("timeout", True)
```

> 《检测变化模式》的使用
```
aioapollo.ApolloConfig("default", "http://192.168.88.103:8080", "SampleApp1","default", "application", aioapollo.ConfigMode.CHECKING)
aioapollo.ApolloConfig("default2", "http://192.168.88.103:8080", "SampleApp2","default", "application", aioapollo.ConfigMode.CHECKING)
aioapollo.ApolloConfig("default3", "http://192.168.88.103:8080", "SampleApp3","default", "application1", aioapollo.ConfigMode.PULL, periodTime=600)
aioapollo.ApolloConfig.startUp()
```
> 其中 aioapollo.ConfigMode.CHECKING 代表是检测变化，你需要在所有配置结束后申明aioapollo.ApolloConfig.startUp()，目的是为了开启线程和异步请求专门对配置信息，进行实时监控
> 例如：
```
apolloClient = aioapollo.ApolloClient("default")
text=await apolloClient.get("timeout")
```
