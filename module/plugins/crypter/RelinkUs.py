#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time

from module.plugins.Crypter import Crypter

class RelinkUs(Crypter):
    __name__ = "RelinkUs"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?relink.us/(f|((view|go).php))"
    __version__ = "1.0"
    __description__ = """Relink.us Container Plugin"""
    __author_name__ = ("Sleeper-", "spoob")
    __author_mail__ = ("@nonymous", "spoob@pyload.org")

    def __init__(self, parent):
        Crypter.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def file_exists(self):
        """ returns True or False
        """
        return True

    def proceed(self, url, location):
        container_id = self.parent.url.split("/")[-1].split("id=")[-1]
        url = "http://relink.us/view.php?id="+container_id
        self.html = self.req.load(url, cookies=True)
        temp_links = []

        # Download Ad-Frames, otherwise we aren't enabled for download
        iframes = re.findall("src=['\"]([^'\"]*)['\"](.*)></iframe>", self.html)
        for iframe in iframes:
            self.req.load("http://relink.us/"+iframe[0], cookies=True)

        link_strings = re.findall(r"onclick=\"getFile\(\'([^)]*)\'\);changeBackgroundColor", self.html)

        for link_string in link_strings:
            self.req.lastURL = url

            # Set Download File
            framereq = self.req.load("http://relink.us/frame.php?"+link_string, cookies=True)

            new_link = self.req.lastEffectiveURL

            if re.match(r"http://(www\.)?relink.us/",new_link):
                # Find iframe
                new_link = re.search("src=['\"]([^'\"]*)['\"](.*)></iframe>", framereq).group(1)
                # Wait some secs for relink.us server...
                time.sleep(5)

            temp_links.append(new_link)

        self.links = temp_links
