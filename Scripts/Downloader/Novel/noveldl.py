import argparse
import asyncio
import time
import aiohttp

# initialize argument parser
from services import download_novel, add_novel_to_library, autoupdate_novels, plog

parser = argparse.ArgumentParser(description='Automated Novel Downloader')
subparsers = parser.add_subparsers(dest="command", help='command')

# start command
start_parser = subparsers.add_parser('start', help='Start autoupdate of novels, runs indefinitely until closed.')
start_parser.add_argument('-i', '--interval', action='store', default=60, dest='interval', type=int, help='Time interval per update')

# add command
add_parser = subparsers.add_parser('add', help='Add new novel to automatically download')
add_parser.add_argument('urls', action='append', help='link to novel to be downloaded automatically')

# download command
download_parser = subparsers.add_parser('download', help='Download novel')
download_parser.add_argument('urls', action='append', help='novels to download')

args = parser.parse_args()
t_start = time.time()
loop = asyncio.get_event_loop()

plog(['ARGUMENTS'], args)
try:
    if args.command == 'download':
        if args.urls:
            for url in args.urls:
                loop.run_until_complete(download_novel(url))

    elif args.command == 'add':
        if args.urls:
            for url in args.urls:
                loop.run_until_complete(add_novel_to_library(url))

    elif args.command == 'start':
        interval = args.interval
        loop.run_until_complete(autoupdate_novels(interval))

except Exception as ex:
    plog(['exception'], '.'.join(['noveldl', str(ex)]))
finally:
    loop.close()


duration = time.time() - t_start
if duration >= 60:
    duration /= 60
    duration = f'{duration:0.2f} min'
else:
    duration = f'{duration:0.2f} s'
plog(['duration'], duration)