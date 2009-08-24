#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from Plugin import Plugin

class HoerbuchIn(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "HoerbuchIn"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?hoerbuch\.in/blog\.php\?id="
        props['version'] = "0.1"
        props['description'] = """Hoerbuch.in Container Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None

    def file_exists(self):
        """ returns True or False
        """
        return True

    def proceed(self, url, location):
        url = self.parent.url
        html = self.req.load(url)
        temp_links = []
        download_container = ("Download", "Mirror #1", "Mirror #2", "Mirror #3")
        for container in download_container:
            download_content = re.search("<BR><B>" + container + ":</B>(.*?)<BR><B>", html).group(1)
            tmp = re.findall('<A HREF="http://www.hoerbuch.in/cj/out.php\?pct=\d+&url=(http://rs\.hoerbuch\.in/.+?)" TARGET="_blank">Part \d+</A>', download_content)
            if tmp == []: continue
            for link in tmp:
                link_html = self.req.load(link, cookies=True)
                temp_links.append(re.search('<FORM ACTION="(http://.*?)" METHOD="post"', link_html).group(1))
            break

        self.links = temp_links
