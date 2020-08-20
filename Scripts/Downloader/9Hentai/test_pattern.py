import re


def check_url(url):
    pattern = r"(https://)?9hentai\.com/g/\d+/?"
    return True if re.match(pattern, url) is not None else False


url = "https://9hentai.com/g/61163/"
print(f"{url} - {check_url(url)}")

url = "https://9hentai.com/g/61163/"
print(f"{url} - {check_url(url)}")

url = "https://9hentai.com/g/61163"
print(f"{url} - {check_url(url)}")

url = "9hentai.com/g/61163"
print(f"{url} - {check_url(url)}")

url = "https://9hentai.com/g/"
print(f"{url} - {check_url(url)}")

url = "9hentai.com/g/"
print(f"{url} - {check_url(url)}")