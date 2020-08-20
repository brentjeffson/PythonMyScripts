import asyncio
import time
from pathlib import Path

import aiohttp

from Scripts.Downloader.Novel.nparse import WuxiaWorldCo
import requests
import re
from bs4 import BeautifulSoup

from Scripts.Downloader.Novel.services import save_content, save


async def get_content_save_function():
    nparse = WuxiaWorldCo()
    resp = requests.get('https://m.wuxiaworld.co/Lord-of-the-Mysteries/2752246.html')
    print(f'[STATUS CODE] {resp.status_code}'
          f'\n[CONTENT LENGTH] {resp.headers["content-length"]}')

    if resp.ok:
        markup = resp.text
        soup = BeautifulSoup(markup, parser='html.parser', features='lxml')
        content = nparse.parse_content(soup)
        await save_content(content, Path('testfile.chapter'))
        print(f'[CONTENT]\n{content}')

async def fetch(session, url):
    stime = time.perf_counter()
    async with session.get(url) as response:
        await response.text()
        return time.perf_counter() - stime

async def arequest_duration(url):
    async with aiohttp.ClientSession() as session:
        tasks = []
        durations = []
        for i in range(10):
            task = asyncio.create_task(fetch(session, url))
            durations.append(await task)
        #     task = asyncio.create_task(fetch(session, url))
        #     tasks.append(task)
        # durations = await asyncio.gather(*tasks)
        print(f'[AVERAGE DURATION] {sum(durations) / len(durations)}')

def request_duration(url):
    durations = []
    for i in range(10):
        start = time.perf_counter()
        content = requests.get(url).text
        duration = time.perf_counter() - start
        durations.append(duration)
        # print(f'[DURATION] {duration:0.2f} s')
    print(f'[AVERAGE DURATION] {sum(durations) / len(durations)}')

def duration_tests():
    url = 'https://www.google.com/'
    print('[SYNCHRONOUS REQUESTS]')
    request_duration(url)

    print('\n[ASYNCHRONOUS REQUESTS]')
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    try:
        loop.run_until_complete(arequest_duration(url))
    except Exception as ex:
        print(ex)
    finally:
        print(f'[DURATION] {time.perf_counter() - start:0.2f} s')
        loop.close()

async def save_data_create_dir_if_not_exists():
    filepath = Path('test_files', 'new.txt')
    await save('', filepath)

if __name__ == '__main__':
    # duration_tests()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(save_data_create_dir_if_not_exists())
    loop.close()
