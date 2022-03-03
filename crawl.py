import aiohttp
import asyncio
import os
import datetime
import json

FARSIGHT_URL = "https://api.dnsdb.info"
API_KEY = "TODO: GET API KEY"

async def query_flex_api(dir_name):
    headers = {"X-API-Key": API_KEY}
    async with aiohttp.ClientSession(FARSIGHT_URL, headers=headers) as session:
        i = 0
        while True:
            current_query = f"/dnsdb/v2/glob/rrset/*._domainkey.*/TXT?offset={i}"
            async with session.get(current_query) as res:
                if not res.ok:
                    break
                with open(f"{dir_name}/offset_{i}.json", "w") as f:
                    async for line in res.content:
                        line = line.decode("utf-8")
                        data = json.loads(line)
                        if "msg" in data.keys() and data["msg"] == "No results found":
                            break
                        f.write(line)
            i += 1


async def query_v2_api(dir_name):
    checked_domains= set()
    files = os.listdir(dir_name)
    headers = {"X-API-Key": API_KEY}
    async with aiohttp.ClientSession(FARSIGHT_URL, headers=headers) as session:
        with open(f"{dir_name}/results.json", "w") as out_file:
            for filename in files:
                path = os.path.join(dir_name, filename)
                print(f"opening file {path}")
                with open(path, "r") as f:
                    for line in f:
                        data = json.loads(line)
                        if "cond" in data.keys():
                            continue

                        domain_name = data["obj"]["rrname"]
                        if domain_name in checked_domains:
                            continue
                        else:
                            checked_domains.add(domain_name)

                        current_query = f"/dnsdb/v2/lookup/rrset/name/{domain_name}/TXT"
                        async with session.get(current_query) as res:
                            async for line in res.content:
                                line = line.decode("utf-8")
                                out_file.write(line)


if __name__ == "__main__":
    timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    dir_name = f"{timestamp}_flex_results"
    os.makedirs(dir_name)

    asyncio.run(query_flex_api(dir_name))
    asyncio.run(query_v2_api(dir_name))
