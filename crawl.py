import aiohttp
import asyncio

FARSIGHT_URL = "https://api.dnsdb.info"
API_KEY = "TODO: GET API KEY"
QUERY = "*._domainkey.*"

async def async_main():
    async with aiohttp.ClientSession(FARSIGHT_URL) as session:
        while TODO_SET_CONDITION:
            async with session.get(f"/dnsdb/v2/lookup/rrnames/{QUERY}") as res:
                json = await res.json()
                print(json)

if __name__ == "__main__":
    asyncio.run(async_main())
