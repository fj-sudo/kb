import asyncio

import requests


async def rq(url):
    response = requests.get(url)
    return response.status_code


async def main():
    gather = await asyncio.gather(rq("http://www.bing.com"), rq("http://www.jd.com"))
    print(gather)


asyncio.run(main())
