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
        download_content = re.search("<BR><B>Download:</B>(.*?)<BR><B>", html).group(1)
        tmp = re.findall('<A HREF="(http://www.hoerbuch.in/cj/out.php\?pct=.*?)" TARGET="_blank">Part \d+</A>', download_content)

        for link in tmp:
            for i in range(5):
                link_html = self.req.load(link, cookies=True)
                link_name = link.split("/")[-1]
                if re.search("<TITLE>(.*)</TITLE>", link_html).group(1) == link_name:
                    link_url = re.search('<FORM ACTION="(http://.*?)" METHOD="post"', link_html).group(1)
                    temp_links.append(link_url)
                    break

        self.links = temp_links
