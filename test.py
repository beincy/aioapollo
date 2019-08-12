import uvloop
import asyncio
import aioapollo


async def main():
    aioapollo.ApolloConfig("default", "http://192.168.88.103:8080", "SampleApp",
                           "default", "application", aioapollo.ConfigMode.CHECKING, periodTime=600)
    aioapollo.ApolloConfig.startUp()
    i = 3600
    while i:
        i -= 1
        a = aioapollo.ApolloClient("default")
        print(await a.get("timeout", True))
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
