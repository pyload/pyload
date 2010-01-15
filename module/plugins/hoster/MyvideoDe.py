# -*- coding: utf-8 -*-

import re
from module.Plugin import Plugin

class MyvideoDe(Plugin):
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "MyvideoDe"
        props['type'] = "hoster"
        props['pattern'] = r"http://(www\.)?myvideo.de/watch/"
        props['version'] = "0.9"
        props['description'] = """Myvideo.de Video Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.url = self.parent.url

    def download_html(self):
        self.html = self.req.load(self.url)

    def get_file_url(self):
        videoId = re.search(r"addVariable\('_videoid','(.*)'\);p.addParam\('quality'", self.html).group(1)
        videoServer = re.search("rel='image_src' href='(.*)thumbs/.*' />", self.html).group(1)
        file_url = videoServer + videoId + ".flv"
        return file_url

    def get_file_name(self):
        file_name_pattern = r"<h1 class='globalHd'>(.*)</h1>"
        return re.search(file_name_pattern, self.html).group(1).replace("/", "") + '.flv'

    def file_exists(self):
        self.download_html()
        self.req.load(str(self.url), cookies=False, just_header=True)
        if self.req.lastEffectiveURL == "http://www.myvideo.de/":
            return False
        return True
