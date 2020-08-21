import asyncio
import json
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

from Scripts.Downloader.Novel.nparse import Novel, Chapter, WuxiaWorldCo, BaseParser, Website, BoxNovelCom
from Scripts.Downloader.Novel.helpers import create_dirs

DOWNLOADS_DIR = 'novels'
LIBRARY_DIR = 'library.inf'


async def get_content(session, chapter, nparse, chapter_path):
    try:
        # get markup
        async with session.get(chapter['url']) as resp:
            if resp.reason:
                # parse content
                markup = await resp.text()
                soup = BeautifulSoup(markup, parser='html.parser', features='lxml')
                content = nparse.parse_content(soup)
                # save content
                await save(content, chapter_path)
                print(f'[{resp.status}][{chapter["id"]}] {chapter["url"]}')
                return 1
    except Exception as ex:
        print(f'[EXCEPTION][{chapter["id"]}] get_content.{ex}:')
        return None


async def save(data, filepath, mode='wt', encoding='utf-8'):
    create_dirs(filepath)
    with open(str(filepath), mode, encoding=encoding) as f:
        f.write(data)


async def save_novel(novel: Novel, filepath: Path) -> None:
    tmp_novel = novel.copy()
    tmp_novel.chapters.clear()
    converted = 0
    # convert Chapter object to a dict
    for chapter in tmp_novel.chapters:
        # check if chapter is a Chapter object
        if type(chapter) == Chapter:
            novel.chapters.append(chapter.to_dict())
            converted += 1
    print(f'[CHAPTERS CONVERTED] {converted}')
    data = json.dumps(tmp_novel.__dict__, indent=4)
    await save(data, filepath)
    # with open(str(filepath), 'wt') as f:
    #     f.write(json.dumps(novel.__dict__, indent=4))


async def load_novel(filepath: Path) -> Novel:
    with open(str(filepath), 'rt') as f:
        jnovel = json.loads(f.read())
        return Novel(
            title=jnovel['title'],
            url=jnovel['url'],
            base_url=jnovel['base_url'],
            meta=jnovel['meta'],
            chapters=jnovel['chapters']
        )


async def add_novel_to_library(url: str, filepath: Path = Path(LIBRARY_DIR).absolute()):
    # clean url for leading and trailing spaces
    url = url.strip()
    # read file if exists
    suffix = ''
    data = await load_novel_library(filepath)
    if data is not None:
        # check if url is already in file
        for u in data.split('\n'):
            if u == url:
                print(f'[URL IN FILE] {url}')
                return -1

        suffix = '\n'
    else:
        data = ''

    # append url to data
    data = f'{suffix}'.join([data, url])
    await save(data, filepath)
    print(f'[SAVED] {len(data)} bytes')


async def load_novel_library(filepath: Path = Path(LIBRARY_DIR).absolute()):
    if filepath.exists():
        with open(filepath, 'rt') as f:
            return f.read()
    else:
        print('[CANNOT LOAD LIBRARY]')
        return None


async def download_novel(url: str):
    # check website source
    nparse = None
    if BaseParser.identify(url) == Website.WUXIAWORLDCO:
        nparse = WuxiaWorldCo()
    elif BaseParser.identify(url) == Website.BOXNOVELCOM:
        nparse = BoxNovelCom()
    else:
        print(f'[UNSUPPORTED WEBSITE] {url}')
        return
    # get markup
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            print(f'[STATUS CODE] {resp.status}')
            if resp.reason.lower() == 'ok':

                # parse markup
                markup = await resp.text()
                soup = BeautifulSoup(markup, parser='html.parser', features='lxml')

                if nparse is not None:
                    # get novel meta
                    meta = nparse.parse_meta(soup)
                    # get new chapters
                    new_chapters = nparse.parse_chapters(soup)
                    # convert Chapter object to dict
                    new_chapters = [chapter.to_dict() for chapter in new_chapters]
                    print(f'[CHAPTER COUNT] {len(new_chapters)}')

                    # get filepath to save novel
                    download_path = Path(DOWNLOADS_DIR, meta.title.replace(' ', '_').upper())
                    novel_path = Path(download_path, ''.join([meta.title.replace(' ', '_').lower(), '.json'])).absolute()

                    # ensure download directory exists
                    if not download_path.exists():
                        download_path.mkdir()

                    # load json file if exists and has data
                    if novel_path.exists() and novel_path.lstat().st_size > 0:
                        # load previous novel download
                        novel = await load_novel(novel_path)
                    else:
                        novel = Novel(
                            title=meta.title,
                            url=url,
                            base_url='/'.join(url.split('/')[:3]),
                            meta=meta.to_dict(),
                            chapters=new_chapters
                        )

                    # add new chapters
                    novel.chapters = new_chapters.copy()
                    await save_novel(novel, novel_path)

                    # check number of undownloaded content
                    undownloaded_count = 0
                    for ref_chapter in new_chapters:
                        cpath = Path(
                            download_path,
                            'contents',
                            ''.join([ref_chapter['url'].split('/')[::-1][0].replace('.html', ''), '.chapter'])
                        )
                        if not cpath.exists():
                            undownloaded_count += 1
                    print(f'[DOWNLOADLOADABLE CONTENT] {undownloaded_count}')

                    # download content
                    tasks = []
                    downloaded = 0
                    for chapter in new_chapters:
                        chapter_path = Path(
                            download_path,
                            'contents',
                            ''.join([chapter['url'].split('/')[::-1][0].replace('.html', ''), '.chapter'])
                        )
                        if not chapter_path.exists():
                            if novel.base_url not in chapter['url']:
                                chapter['url'] = ''.join([novel.base_url, chapter['url']])
                            task = asyncio.create_task(get_content(session, chapter, nparse, chapter_path))
                            tasks.append(task)

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        if result is not None:
                            downloaded += 1
                    print(f'[DOWNLOADED] {downloaded}')


async def autoupdate_novels(interval: int):
    async with aiohttp.ClientSession() as session:
        running = True
        while running:
            try:
                data = await load_novel_library()
                if data is not None:
                    # split data into individual lines containing url
                    for url in data.split('\n'):
                        print(f'\n[UPDATING] {url}')
                        # start download process
                        task = asyncio.create_task(download_novel(url))
                        await task
                else:
                    print('[NOVEL LIBRARY MISSING]')
                    break

                for i in range(interval):
                    print(f'[WAITING] {interval-i} s', end='\r')
                    await asyncio.sleep(1)
            except Exception as ex:
                print(f'[EXCEPTION] autoupdate_novels.{ex}')
                print(f'[RETRYING]')
