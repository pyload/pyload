#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time

from Plugin import Plugin

class RelinkUs(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "RelinkUs"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?relink.us/(f|((view|go).php))"
        props['version'] = "0.2"
        props['description'] = """Relink.us Container Plugin"""
        props['author_name'] = ("Sleeper-")
        props['author_mail'] = ("@nonymous")
        self.props = props
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

        print new_link
        temp_links.append(new_link)

    self.links = temp_links
