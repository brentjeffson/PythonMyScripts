import asyncio
import json
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

from nparse import Novel, Chapter, WuxiaWorldCo, BaseParser, Website, BoxNovelCom
from helpers import create_dirs, plog

DOWNLOADS_DIR = 'novels'
LIBRARY_DIR = 'library.inf'


async def get_parsed_markup(session: aiohttp.ClientSession, url: str):
    """Get markup of **url**

    Args:
        session (aiohttp.ClientSession): Session to get markup of url
        url (str): URL of website to get markup

    Returns:
        tuple: (BeautifulSoup, int) for success, else (None, int)
    """
    async with session.get(url) as resp:
        if resp.reason.lower() == 'ok':
            return BeautifulSoup(await resp.text(), parser='html.parser', features='lxml'), resp.status
        else:
            return None, resp.status


async def get_chapter_content(session: aiohttp.ClientSession, chapter: Chapter, nparse: BaseParser):
    """
    Get content of **chapter**

    :param session: Session used to get markup of chapter
    :type session: aiohttp.ClientSession
    :param chapter: Instance of **Chapter**
    :type chapter: Chapter
    :param nparse: Parser used to parsed content from chapter
    :type nparse: BaseParser
    :returns: **(content, status, chapter)** if the markup is parsed successfully, else **(None, status, chapter)**
    :rtype: str

    """
    soup, status = await get_parsed_markup(session, chapter.url)
    if soup is not None:
        content = nparse.parse_content(soup)
        return content, status, chapter
    else:
        return None, status, chapter


async def get_novel(session: aiohttp.ClientSession, url: str, nparse: BaseParser):
    """parse meta, chapters from the novel homepage, and return Novel"""
    # get parsed markup
    soup, status = await get_parsed_markup(session, url)
    if soup is not None:
        meta = nparse.parse_meta(soup)
        chapters = nparse.parse_chapters(soup)
        return Novel(
            meta.title,
            url,
            '/'.join(url.split('/')[:3]),
            meta,
            chapters
        ), status
    else:
        return None, status


async def save(data: str, filepath: Path, mode: str = 'wt', encoding: str = 'utf-8'):
    """
    Save **data** to **filepath**

    :param data: Contains data to be saved
    :type data: str
    :param filepath: Path to the file where **data** will be saved
    :type filepath: Path
    :param mode: Mode to upon which the file opened
    :type mode: str
    :param encoding: Encoding to encode write data to file
    :return: None
    """
    create_dirs(filepath)
    with filepath.open(mode=mode, encoding=encoding) as f:
        f.write(data)
    # with open(str(filepath), mode, encoding=encoding) as f:
    #     f.write(data)


async def save_novel(novel: Novel, filepath: Path):
    """
    Save **novel** to **filepath**

    :param novel: Instance of **Novel** to be saved in **filepath
    :type novel: Novel
    :param filepath: Path to a file containing information on the **novel**
    :returns: Number of chapter converted from **Chapter** object to **dict**
    :rtype: int
    """
    # convert Chapter object to a dict
    converted_chapters = [chapter.to_dict() if type(chapter) == Chapter else chapter for chapter in novel.chapters]

    data = json.dumps(Novel(
        novel.title,
        novel.url,
        novel.base_url,
        novel.meta.to_dict(),
        converted_chapters
    ).__dict__, indent=4)
    await save(data, filepath)
    return len(converted_chapters)


async def load_novel(filepath: Path) -> Novel:
    """
    Load information containing novel details

    :param filepath: Path to novel information
    :type filepath: Path
    :returns: An instance of Novel
    :rtype: Novel
    """
    with open(str(filepath), 'rt') as f:
        novel_dictionary = json.loads(f.read())
        return Novel(
            title=novel_dictionary['title'],
            url=novel_dictionary['url'],
            base_url=novel_dictionary['base_url'],
            meta=novel_dictionary['meta'],
            chapters=novel_dictionary['chapters']
        )


async def add_novel_to_library(url: str, filepath: Path = Path(LIBRARY_DIR).absolute()):
    """
    Add **url** to novel library indicated by **filepath**

    :param url: URL to be added to novel library
    :type url: str
    :param filepath: Path to novel library
    :type filepath: Path
    :returns: If url is saved returns **data**, otherwise **None**
    :rtype: str
    """
    # clean url for leading and trailing spaces
    new_url = url.strip()
    # read file if exists
    suffix = ''
    data = await load_novel_library(filepath)
    if data is not None:
        # check if url is already in file
        for u in data.split('\n'):
            if u == new_url:
                plog(['in library'], new_url)
        suffix = '\n'
    else:
        return None

    # append url to data
    data = f'{suffix}'.join([data, url])
    await save(data, filepath)
    plog(['saved'], f'{len(data)} bytes')
    return data


async def load_novel_library(filepath: Path = Path(LIBRARY_DIR).absolute()):
    """
    Load novel library containing a list of novels

    :param Path filepath: Path location to the novels library
    :returns: if filepath exists return a **string** containing a list of novels, otherwise **None**
    :rtype: str
    """
    if filepath.exists():
        with open(filepath, 'rt') as f:
            return f.read()
    else:
        plog(['MISSING FILE'], filepath)
        return None


# todo seperate work to different functions
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
        novel, status = await get_novel(session, url, nparse)
        plog([status], url)
        if novel is not None:

            plog(['chapter count'], len(novel.chapters))

            # get filepath to save novel
            download_path = Path(DOWNLOADS_DIR, novel.meta.title.replace(' ', '_').upper())
            novel_path = Path(download_path, ''.join([novel.meta.title.replace(' ', '_').lower(), '.json'])).absolute()

            # ensure download directory exists
            if not download_path.exists():
                download_path.mkdir()

            # load json file if exists and has data
            if novel_path.exists() and novel_path.lstat().st_size > 0:
                # load previous novel information
                # novel = await load_novel(novel_path)

                # save novel information
                converted_chapters = await save_novel(novel, novel_path)
                plog(['chapter -> dict'], converted_chapters)

                # check number of undownloaded content
                amount_to_download = 0
                for chapter in novel.chapters:
                    cpath = Path(
                        download_path,
                        'contents',
                        ''.join([chapter.url.split('/')[::-1][0].replace('.html', ''), '.chapter'])
                    )
                    if not cpath.exists():
                        amount_to_download += 1
                plog(['# downloads'], amount_to_download)

                # create tasks to download content
                tasks = []
                for chapter in novel.chapters:
                    chapter_path = Path(
                        download_path,
                        'contents',
                        ''.join([chapter.url.split('/')[::-1][0].replace('.html', ''), '.chapter'])
                    )
                    if not chapter_path.exists():
                        chapter.url = ''.join([novel.base_url, chapter.url]) if novel.base_url not in chapter.url else chapter.url
                        task = asyncio.create_task(get_chapter_content(session, chapter, nparse))
                        tasks.append(task)

                # process completed content download
                bytes_downloaded = 0
                downloaded = 0
                for future in asyncio.as_completed(tasks):
                    try:
                        content, status, chapter = await future
                        chapter_path = Path(
                            download_path,
                            'contents',
                            ''.join([chapter.url.split('/')[::-1][0].replace('.html', ''), '.chapter'])
                        )
                        if content is not None:
                            downloaded += 1
                            await save(content, chapter_path)
                            bytes_downloaded += len(content)
                            plog([status, chapter.id], f'{len(content)} b - {chapter.url}')

                    except aiohttp.ServerConnectionError as e:
                        plog(['retry'])
                        chapter.url = ''.join(
                            [novel.base_url, chapter.url]) if novel.base_url not in chapter.url else chapter.url
                        task = asyncio.create_task(get_chapter_content(session, chapter, nparse))
                        tasks.append(task)

                plog(['downloaded'], downloaded)


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
                # print('\n')
                for i in range(interval):
                    print(f'[WAITING] {interval-i} s', end='\r')
                    await asyncio.sleep(1)
                    print(' '*len(f'[WAITING] {interval - i} s'), end='\r')
            except KeyboardInterrupt as ex:
                plog(['exiting'])
            except aiohttp.ServerConnectionError as e:
                plog(['retrying'])
