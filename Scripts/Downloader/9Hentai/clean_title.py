import re

raw_title = "[Dekochin Hammer] Shishunki RIOT - Puberty Riot Ch. 1-4 [English] {Mistvern} [Digital]"

def clean_title(title):
    pattern = r"[\[\{]+[\w\s]+[\]\}]+"
    new_title = re.sub(pattern, "", title).strip().replace(" ", "_")
    pattern = r"[\?\W]+"
    new_title = re.sub(pattern, "", new_title)
    return new_title

print(clean_title(raw_title))