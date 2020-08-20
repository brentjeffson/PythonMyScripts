import requests
import json
from pprint import pprint


proxies = {
    "http": "http://192.168.43.1:44355",
    "https": "https://192.168.43.1:44355"
}
url = str(input("> "))
resp = requests.head(url, proxies=proxies)

for val, key in resp.headers.items():
    print(f'{val}: {key}')









