# -*- coding: utf-8 -*-

from ..base.decrypter import BaseDecrypter

import re
import json
import os
from urllib.parse import quote, urlparse


class KnigavuheOrgFolder(BaseDecrypter):
    __name__ = "KnigavuheOrgFolder"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"
    __pattern__ = r"https?:\/\/knigavuhe\.org\/book\/.+"

    __authors__ = [("EnergoStalin", "ens.stalin@gmail.com")]
    __license__ = "GPLv3"

    BOOK_PLAYER_DATA_PATTERN = r"new BookPlayer\(\d+,\s?(\[.+?\]),"
    BOOK_TITLE_PATTERN = r"book = ({.+});"
    BOOK_AUTHOR_PATTERN = r"<a href=\"\/author\/.+?\/\">\s*(.+?)<\/a>"
    VOLUME_PATTERN = r"((?:\d+.?)\d+)\.<\/span>\s+<strong>{}"
    COVER_PATTERN = r"https:\/\/s\d+\.knigavuhe\.org\/\d+\/covers\/\d+\/1-2\.jpg\?\d+"

    def _get_book_title(self, html):
        text = re.search(self.BOOK_TITLE_PATTERN, html)
        if not text:
            self.fail("Could not find title.")

        title = json.loads(text[1])["name"]
        volume = re.search(self.VOLUME_PATTERN.format(title), html)
        if volume:  # If single volume omit number in series
            title = f"{volume.group(1)}. {title}"

        return title

    def _get_book_data(self, html):
        text = re.search(self.BOOK_PLAYER_DATA_PATTERN, html)
        if not text:
            self.fail("Could not find BookPlayer data.")

        return json.loads(text.group(1))

    def _get_book_author(self, html):
        text = re.search(self.BOOK_AUTHOR_PATTERN, html)
        if not text:
            self.log_warning("Could not find author.")
            return None

        return text.group(1)

    def _check_exists(self, url):
        headers = self.load(url, just_header=True)
        return "code" in headers and headers.get("code") == 200

    def _get_book_cover(self, html):
        text = re.search(self.COVER_PATTERN, html)
        if not text:
            self.log_warning("Could not find cover.")
            return None

        cover = text.group()

        # Might work might not discovered by manual experimenting
        bigger_cover = cover.replace("1-2", "1-4")
        if self._check_exists(bigger_cover):
            return bigger_cover

        if self._check_exists(cover):
            return cover

        self.fail("Can't download cover while url is present.")

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)
        data = self._get_book_data(html)
        title = self._get_book_title(html)
        author = self._get_book_author(html)
        cover = self._get_book_cover(html)

        if not data or not title:
            self.fail("No book data or title found.")

        urls = [f"{x['url']}#{quote(x['title'] + os.path.splitext(urlparse(x['url']).path)[1])}" for x in data]
        if cover: urls.append(f"{cover}#cover.jpg")

        package_folder = title
        if author: package_folder = f"{author} - {package_folder}"

        self.packages.append(
            (
                title,
                urls,
                package_folder,
            )
        )
