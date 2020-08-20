from network.youtube import Youtube
import requests
import json
from pathlib import Path
import os

filename = os.path.join(Path.cwd(), 'types.json')
html_filename = 'html.html'
urls = [
    '4mnaXZGp9uc',
    'PiWDylHIoRk',
    'rYa3DuLjNwY',
    'HoEcEbgJuik',
    'QougB4t6TWU',
]
youtube_api = 'https://www.youtube.com/watch'

if not Path(html_filename).exists():
    resp = requests.get(youtube_api, params={'v': urls[0]})
    print(resp.status_code)
    if resp.ok:
        html = resp.text
        with open(html_filename, 'wt', encoding=resp.encoding) as f:
            f.write(html)
    
else:
    with open(html_filename, 'rt', encoding='utf-8') as f:
        html = f.read()

sources = Youtube.get_sources(html)
temp_types = {}
for source in sources:
    sourceType = source["mimeType"].split(';')[0]
    if 'qualityLabel' in source and 'video' in sourceType:
        if sourceType in temp_types:
            if source['qualityLabel'] in temp_types[sourceType]:
                temp_types[sourceType][source['qualityLabel']].append(f'{source["itag"]};{source["mimeType"]}')
            else:
                temp_types[sourceType].update({source['qualityLabel']: []})
                temp_types[sourceType][source['qualityLabel']].append(f'{source["itag"]};{source["mimeType"]}')
        else:
            temp_types.update({sourceType: {}})
            if source['qualityLabel'] in temp_types[sourceType]:
                temp_types[sourceType][source['qualityLabel']].append(f'{source["itag"]};{source["mimeType"]}')
            else:
                temp_types[sourceType].update({source['qualityLabel']: []})
                temp_types[sourceType][source['qualityLabel']].append(f'{source["itag"]};{source["mimeType"]}')
        
    elif 'audioQuality' in source and 'audio' in sourceType:
        if sourceType in temp_types:
            if source['audioQuality'] in temp_types[sourceType]:
                temp_types[sourceType][source['audioQuality']].append(f'{source["itag"]};{source["mimeType"]}')
            else:
                temp_types[sourceType].update({source['audioQuality']: []})
                temp_types[sourceType][source['audioQuality']].append(f'{source["itag"]};{source["mimeType"]}')
        else:
            temp_types.update({sourceType: {}})
            if source['audioQuality'] in temp_types[sourceType]:
                temp_types[sourceType][source['audioQuality']].append(f'{source["itag"]};{source["mimeType"]}')
            else:
                temp_types[sourceType].update({source['audioQuality']: []})
                temp_types[sourceType][source['audioQuality']].append(f'{source["itag"]};{source["mimeType"]}')
with open(filename, 'wt') as f:
    f.write(json.dumps(temp_types, indent=4))



