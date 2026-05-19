import asyncio
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat

async def async_fetch(session: aiohttp.ClientSession, url: str) -> str:
    """
    Asyncronously fetch (get-request) single url using provided session
    :param session: aiohttp session object
    :param url: target http url
    :return: fetched text
    """
    async with session.get(url) as result:
        return await result.text()

async def async_requests(urls: list[str]) -> list[str]:
    """
    Concurrently fetch provided urls using aiohttp
    :param urls: list of http urls ot fetch
    :return: list of fetched texts
    """
    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(*[async_fetch(session, x) for x in urls])
        return list(result)

def sync_fetch(session: requests.Session, url: str) -> str:
    """
    Syncronously fetch (get-request) single url using provided session
    :param session: requests session object
    :param url: target http url
    :return: fetched text
    """
    return session.get(url).text

def threaded_requests(urls: list[str]) -> list[str]:
    """
    Concurrently fetch provided urls with requests in different threads
    :param urls: list of http urls ot fetch
    :return: list of fetched texts
    """
    with requests.Session() as sess:
        with ThreadPoolExecutor(len(urls)) as executer:
            return list(executer.map(sync_fetch, repeat(sess), urls))
