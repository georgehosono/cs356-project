import aiohttp
import asyncio
import os
import datetime
import json
import logging

FARSIGHT_URL = "https://api.dnsdb.info"
API_KEY = "TODO: GET API KEY"
LIMIT = 100000

# global logging state
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
# filepath will be changed before first use.
handler = logging.FileHandler('tmp_log')
logger.addHandler(handler)

def change_output_file(new_filepath):
    global logger
    global handler
    global formatter
    logger.removeHandler(handler)
    handler = logging.FileHandler(new_filepath)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# flex api allows double-ended wildcards, which we need in order to find
# arbitrary selectors on arbitrary domains.
async def query_flex_api(dir_name):
    global LIMIT
    global API_KEY
    global FARSIGHT_URL
    headers = {"X-API-Key": API_KEY}
    async with aiohttp.ClientSession(FARSIGHT_URL, headers=headers) as session:
        i = 0
        while True:
            current_query = f"/dnsdb/v2/glob/rrset/*._domainkey.*/TXT?limit={LIMIT}&offset={i}"
            async with session.get(current_query) as res:
                if not res.ok:
                    break

                # write output. using logging module since it is thread safe
                # and regular file writes are not.
                change_output_file(f"{dir_name}/offset_{i}.json")
                async for line in res.content:
                    line = line.decode("utf-8")
                    data = json.loads(line)
                    if "msg" in data.keys() and data["msg"] == "No results found":
                        break
                    logger.info(line)
            i += 1

# v2 api provides useful information that flex api does not.
async def query_v2_api(dir_name):
    global API_KEY
    global FARSIGHT_URL
    checked_domains= set()
    files = os.listdir(dir_name)
    headers = {"X-API-Key": API_KEY}
    async with aiohttp.ClientSession(FARSIGHT_URL, headers=headers) as session:
        change_output_file(f"{dir_name}/results.json")
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
                            logger.info(line)

if __name__ == "__main__":
    timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    dir_name = f"{timestamp}_flex_results"
    os.makedirs(dir_name)

    # this first call will populate the directory with one file per successfully
    # queried offset. Each file contains newline-delimited JSON.
    await asyncio.run(query_flex_api(dir_name))

    # this function will read the files in the directory and populate a single
    # newline-delimited JSON file with the richer results for each selector
    # query identified in the first call.
    await asyncio.run(query_v2_api(dir_name))

