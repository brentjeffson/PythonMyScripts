import re
import requests
import json
def get_book_info(url):
    s_url = url.split("/")
    book_id = s_url[len(s_url)-2] if s_url[len(s_url)-1] == "" else s_url[len(s_url)-1]
    resp = requests.post("https://9hentai.com/api/getBookByID", params={"id": book_id})
    print(resp)
    print(resp.content)
    info = json.loads(resp.content)
    print(info)

url = "https://9hentai.com/g/61128/"
s_url = url.split("/")
book_id = s_url[len(s_url)-2] if s_url[len(s_url)-1] == "" else s_url[len(s_url)-1]
get_book_info(url)