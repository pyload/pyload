# -*- coding: utf-8 -*-

from ..base.decrypter import BaseDecrypter

import re
import json
import os


class KnigavuheOrg(BaseDecrypter):
    __name__ = "KnigavuheOrg"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"
    __pattern__ = r"https?:\/\/knigavuhe\.org\/book\/.+"

    __authors__ = [("EnergoStalin", "ens.stalin@gmail.com")]
    __license__ = "GPLv3"

    BOOK_PLAYER_DATA_PATTERN = r"new BookPlayer\(\d+,\s?(\[.+?\]),"
    BOOK_TITLE_PATTERN = r"book = ({.+});"
    VOLUME_PATTERN = r"((?:\d+.?)\d+)\.<\/span>\s+<strong>{}"
    COVER_PATTERN = r"https:\/\/s2\.knigavuhe\.org\/2\/covers\/\d+\/1-2\.jpg\?1"

    def _get_book_title(self, html):
        text = re.search(self.BOOK_TITLE_PATTERN, html)
        if not text:
            self.fail("Could not obtain title.")
            return

        title = json.loads(text[1])["name"]
        volume = re.search(self.VOLUME_PATTERN.format(title), html)
        if volume:  # If single volume omit number in series
            title = f"{volume.group(1)}. {title}"

        return title

    def _get_book_data(self, html):
        text = re.search(self.BOOK_PLAYER_DATA_PATTERN, html)
        if not text:
            self.fail("Could not find BookPlayer data.")
            return

        return json.loads(text.group(1))

    def _get_book_cover(self, html):
        text = re.search(self.COVER_PATTERN, html)
        if not text:
            self.fail("Could not find cover url.")
            return

        s, e = text.span()
        return html[s:e]

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)
        data = self._get_book_data(html)
        title = self._get_book_title(html)
        cover = self._get_book_cover(html)

        if not data or not title:
            return

        urls = [f"{x['url']}#{x['title']}{os.path.splitext(x['url'])[1]}" for x in data]
        urls.append(f"{cover}#cover.jpg")

        package = pyfile.package()
        self.packages.append(
            (
                title or package.name,
                urls,
                title or package.folder,
            )
        )
