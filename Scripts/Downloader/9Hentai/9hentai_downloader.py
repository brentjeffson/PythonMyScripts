import requests
import json
import concurrent.futures
import re
import os
from os import path, stat

from requests.exceptions import SSLError

PROXY = {
    "http": "http://192.168.43.1:44355",
    "https": "https://192.168.43.1:44355"
}
VERIFY = False
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
}


def get_book_info(url):
    s_url = url.split("/")
    book_id = s_url[len(s_url)-2] if s_url[len(s_url)-1] == "" else s_url[len(s_url)-1]
    resp = requests.post("https://9hentai.com/api/getBookByID", headers=HEADERS, data={"id": book_id}, verify=VERIFY)
    
    info = json.loads(resp.content)
    return info


def create_image_urls(book_info):
    img_urls = []

    book_id = book_info["results"]["id"]
    total_pages = int(book_info["results"]["total_page"])
    image_server = book_info["results"]["image_server"]
    file_extension = "jpg"

    for page in range(total_pages):
        img_urls.append(f"{image_server}{book_id}/{page + 1}.{file_extension}")

    return img_urls


def clean_title(title):
    pattern = r"[\[\{]+[\w\s]+[\]\}]+"
    new_title = re.sub(pattern, "", title).strip().replace(" ", "_")
    pattern = r"[\?\W]+"
    new_title = re.sub(pattern, "", new_title)
    return new_title


def is_resumable(url):
    headers = requests.head(url).headers
    return "accept-ranges" in headers, headers['content-length']


def download(url, save_dir):
    headers = {}
    write_type = "wb"

    if not path.exists(save_dir): 
        os.mkdir(save_dir)

    # create filename from url
    url_list = url.split('/')
    file_name = url_list[len(url_list) - 1]

    # check if file already exists
    if path.exists(file_name):
        file_size = stat(file_name).st_size
        resumable = is_resumable(url)
        # check if file has already been downloaded
        if file_size == int(resumable[1]):
            # dont download
            print(f"Already downloaded...")
            return True, url
        elif resumable[0]:
            # resume if possible
            headers = {'range': f'bytes={file_size}'}
            write_type = "ab"
            print(f"Resuming Download From: {file_size}")
        else:
            # download from start
            print(f"Unable To Resume...Re-Downloading...")

    resp = requests.get(url, headers=headers, verify=VERIFY)
    if resp.ok:
        with open(os.path.join(save_dir, file_name), write_type) as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)
            return True, url
    else:
        return False, url


def check_url(url):
    pattern = r"(https://)?9hentai\.com/g/\d+/?"
    return True if re.match(pattern, url) is not None else False


while True:
    url = input("URL> ")
    if check_url(url):
        while True:
            try:
                book_info = get_book_info(url)
                break
            except SSLError as e:
                print("SSLError: Retrying")
                continue

        img_urls = create_image_urls(book_info)
        save_dir = os.path.join('..\\..\\..', 'Downloads', clean_title(book_info["results"]["title"]))

        with concurrent.futures.ThreadPoolExecutor(12) as executor:
            print(f"Downloading {book_info['results']['total_page']} Images")
            results = [executor.submit(download, url, save_dir) for url in img_urls]
        
            for future_res in concurrent.futures.as_completed(results):
                print(future_res.result())

        

