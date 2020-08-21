import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from bs4 import BeautifulSoup


class Website(Enum):
    WUXIAWORLDCO = 'wuxiaworld.co'
    BOXNOVELCOM = 'boxnovel.com'


class Status(Enum):
    ONGOING = 1
    COMPLETED = 2


@dataclass
class Selectors:
    title: str
    chapters: str
    content: str
    authors: str
    genres: str
    description: str
    rating: str
    status: str


@dataclass
class Item:
    title: str
    url: str


@dataclass
class Meta:
    title: str
    description: str
    rating: float
    authors: List = field(default_factory=list)
    genres: List = field(default_factory=list)
    status: Status = Status.ONGOING

    def to_dict(self):
        return self.__dict__


@dataclass
class Chapter(Item):
    id: str
    # content: str = ''

    def to_dict(self):
        return self.__dict__
        # return {
        #     'id': self.id,
        #     'title': self.title,
        #     'url': self.url,
        #     # 'content': self.content,
        # }

    @staticmethod
    def from_dict(chapter):
        return Chapter(
            id=chapter['id'],
            title=chapter['title'],
            url=chapter['url'],
            # content=dict['content'],
        )


@dataclass
class Novel(Item):
    base_url: str
    title: str
    url: str
    meta: Meta
    chapters: List = field(default_factory=list)

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(novel):
        return Novel(
            title=novel['title'],
            url=novel['url'],
            base_url=novel['base_url'],
            meta=novel['meta'],
            chapters=novel['chapters']
        )

    def copy(self):
        return Novel(
            self.title,
            self.url,
            self.base_url,
            self.meta,
            self.chapters
        )

class BaseParser:

    def __init__(self, title_selector: str,
                 chapters_selector: str, content_selector: str,
                 authors_selector: str, genres_selector: str,
                 description_selector: str,
                 rating_selector: str, status_selector: str):
        self.__chapter_selector = chapters_selector
        self.__content_selector = content_selector
        self.__authors_selector = authors_selector
        self.__genres_selector = genres_selector
        self.__description_selector = description_selector
        self.__title_selector = title_selector
        self.__rating_selector = rating_selector
        self.__status_selector = status_selector

    @staticmethod
    def identify(url):
        website = None
        if Website.WUXIAWORLDCO.value in url:
            website = Website.WUXIAWORLDCO
        elif Website.BOXNOVELCOM.value in url:
            website = Website.BOXNOVELCOM
        return website

    def parse_meta(self, soup: BeautifulSoup) -> Meta:
        title = self._parse_element_text(soup, self.__title_selector)
        authors = self._parse_list_element_text(soup, self.__authors_selector)
        genres = self._parse_list_element_text(soup, self.__genres_selector)
        description = self._parse_element_text(soup, self.__description_selector)
        rating = self._parse_element_text(soup, self.__rating_selector)
        status = (self._parse_element_text(soup, self.__status_selector).lower() == Status.ONGOING.name.lower()) \
            if Status.ONGOING else Status.COMPLETED
        return Meta(title, description, float(rating), authors, genres, status)

    def _parse_element_text(self, soup, selector) -> str:
        element = soup.select_one(selector)
        return element.text

    def _parse_list_element_text(self, soup, selector) -> List:
        elements = soup.select(selector)
        items = []
        for element in elements:
            items.append(element.text)
        return items

    def parse_chapters(self, soup: BeautifulSoup) -> List[Chapter]:
        chapter_elements = soup.select(self.__chapter_selector)
        chapters = []
        for element in chapter_elements:
            chapter_title = element.text
            chapter_id = re.findall('([\d\.]+)', chapter_title)[0]
            chapter_url = element['href']
            chapters.append(Chapter(id=chapter_id, title=chapter_title, url=chapter_url))
        return chapters

    def parse_content(self, soup: BeautifulSoup) -> str:
        return '\n'.join(self._parse_list_element_text(soup, self.__content_selector))


class WuxiaWorldCo(BaseParser):
    SELECTORS = Selectors(
        'div.book-info > div.book-name',
        'a.chapter-item', 'div.chapter-entity',
        'div.author > span.name', 'div.book-catalog > span.txt',
        'div.content > p.desc', 'span.score', 'div.book-state > span.txt'
    )

    def __init__(self):
        super(WuxiaWorldCo, self).__init__(
            self.SELECTORS.title,
            self.SELECTORS.chapters, self.SELECTORS.content,
            self.SELECTORS.authors, self.SELECTORS.genres,
            self.SELECTORS.description, self.SELECTORS.rating, self.SELECTORS.status
        )

    def parse_chapters(self, soup: BeautifulSoup) -> List:
        chapters = super().parse_chapters(soup)
        # reverse order from descending to ascending
        chapters = chapters[::-1]
        return chapters

    def parse_content(self, soup: BeautifulSoup) -> str:
        content_element = soup.select_one(self.SELECTORS.content)
        content = content_element.text\
            .replace('(adsbygoogle = window.adsbygoogle || []).push({});', '') \
            .replace('\r\n', '').replace('  ', '').replace('\n\n\n', '').replace('\n\n\n\n', '')
            # .replace('\r\n', '').replace(' ' * 24, '').replace('<br/>', '\n')

        return content


class BoxNovelCom(BaseParser):
    SELECTORS = Selectors(
        'ol.breadcrumb > li:last-child',
        'li.wp-manga-chapter > a', 'div.cha-words p ::: div.text-left > p',
        'div.author-content > a', 'div.genres-content',
        'div#editdescription', 'div.post-total-rating > span.total_votes',
        'div.post-status > div:nth-child(2) > div:last-child'
    )

    def __init__(self):
        super(BoxNovelCom, self).__init__(
            self.SELECTORS.title,
            self.SELECTORS.chapters, self.SELECTORS.content,
            self.SELECTORS.authors, self.SELECTORS.genres,
            self.SELECTORS.description, self.SELECTORS.rating, self.SELECTORS.status
        )

    def parse_meta(self, soup: BeautifulSoup) -> Meta:
        meta =  super().parse_meta(soup)
        meta.genres = [genre.replace('\n', '') for genre in meta.genres]
        meta.authors = [author.replace('\n', '') for author in meta.authors]
        meta.description = meta.description[1:]
        meta.title = meta.title.replace('\n', '').replace('\r', '').replace('\t', '').strip()
        return meta

    def parse_chapters(self, soup: BeautifulSoup) -> List[Chapter]:
        chapters = super().parse_chapters(soup)
        for chapter in chapters:
            chapter.title = chapter.title.replace('\t', '').replace('\n', '').strip()
        return chapters

    def parse_content(self, soup: BeautifulSoup) -> str:
        paragraph_elements = soup.select(self.SELECTORS.content.split(':::')[0].strip())
        if len(paragraph_elements) == 0:
            paragraph_elements = soup.select(self.SELECTORS.content.split(':::')[1].strip())
        content_list = [element.text for element in paragraph_elements]
        return '\n'.join(content_list)