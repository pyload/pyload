#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib import unquote
from module.plugins.Hoster import Hoster


class DailymotionCom(Hoster):
    __name__ = 'DailymotionCom'
    __type__ = 'hoster'
    __pattern__ = r'http://www.dailymotion.com/.*'
    __version__ = '0.11'
    __description__ = """Dailymotion Video Download Hoster"""
    __author_name__ = ("Peekayy")
    __author_mail__ = ("peekayy.dev@gmail.com")

    def process(self, pyfile):
        html = self.load(pyfile.url, decode=True)

        for pattern in (r'name="title" content="Dailymotion \\-(.*?)\\- ein Film',
                        r'class="title" title="(.*?)"',
                        r'<span class="title foreground" title="(.*?)">',
                        r'"(?:vs_videotitle|videoTitle|dm_title|ss_mediaTitle)": "(.*?)"'):
            filename = re.search(pattern, html)
            if filename is not None:
                break
        else:
            self.fail("Unable to find file name")

        pyfile.name = filename.group(1) + '.mp4'
        self.logDebug('Filename=' + pyfile.name)
        allLinksInfo = re.search(r'"sequence":"(.*?)"', html)
        self.logDebug(allLinksInfo.groups())
        allLinksInfo = unquote(allLinksInfo.group(1))

        for quality in ('hd720URL', 'hqURL', 'sdURL', 'ldURL', ''):
            dlLink = self.getQuality(quality, allLinksInfo)
            if dlLink is not None:
                break
        else:
            self.fail(r'Unable to find video URL')

        self.logDebug(dlLink)
        self.download(dlLink)

    def getQuality(self, quality, data):
        link = re.search('"' + quality + '":"(http:[^<>"\']+)"', data)
        if link is not None:
            return link.group(1).replace('\\', '')
