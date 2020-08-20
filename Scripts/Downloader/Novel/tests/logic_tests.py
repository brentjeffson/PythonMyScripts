import asyncio

from Scripts.Downloader.Novel.nparse import Novel
import json

from Scripts.Downloader.Novel.services import add_novel_to_library


def saving_object_to_json_file():
    novel = Novel('Lord', 'url', 'base', [1, 2, 3])
    with open('saving_object_to_json_file.json', 'wt') as f:
        f.write(json.dumps(novel.__dict__))

def load_json_string_to_object():
    with open('saving_object_to_json_file.json', 'rt') as f:
        jnovel = json.loads(f.read())
        novel = Novel(jnovel['title'], jnovel['url'], jnovel['base_url'], jnovel['chapters'])
        print(novel)

async def save_and_load_library():
    await add_novel_to_library('https://m.wuxiaworld.co/Lord-of-the-Mysteries/2752246.html')

if __name__ == '__main__':
    # saving_object_to_json_file()
    # load_json_string_to_object()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(save_and_load_library())
    except Exception as ex:
        print(f'[EXCEPTION] {ex}')
    finally:
        loop.close()