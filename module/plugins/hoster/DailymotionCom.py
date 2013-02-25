#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib import unquote
from module.plugins.Hoster import Hoster

class DailymotionCom(Hoster):
    __name__ = 'DailymotionCom'
    __type__ = 'hoster'
    __pattern__ = r'http://www.dailymotion.com/.*'
    __version__ = '0.1'
    __description__ = """Dailymotion Video Download Hoster"""
    __author_name__ = ("Peekayy")
    __author_mail__ = ("peekayy.dev@gmail.com")

    def process(self, pyfile):
        html = self.load(pyfile.url, decode=True)

        filename = re.search(r'name="title" content="Dailymotion \\-(.*?)\\- ein Film', html)
        if filename is None:
            filename = re.search(r'<span class="title foreground" title="(.*?)">', html)
            if filename is None:
                filename = re.search(r'class="title" title="(.*?)"', html)
                if filename is None:
                    filename = re.search(r'"(?:vs_videotitle|videoTitle|dm_title|ss_mediaTitle)": "(.*?)"', html)
                    if filename is None:
                        self.fail("Unable to find file name")
        pyfile.name = filename.group(1)+'.mp4'
        self.logDebug('Filename='+pyfile.name)
        allLinksInfo = re.search(r'"sequence":"(.*?)"', html)
        self.logDebug(allLinksInfo.groups())
        allLinksInfo = unquote(allLinksInfo.group(1))
        
        dlLink = self.getQuality('hd720URL', allLinksInfo)
        if dlLink is None:
            dlLink = self.getQuality('hqURL', allLinksInfo)
            if dlLink is None:
                dlLink = self.getQuality('sdURL', allLinksInfo)
                if dlLink is None:
                    dlLink = self.getQuality('ldURL', allLinksInfo)
        if dlLink is None:
            self.fail(r'Unable to find video URL')
        else:
            self.logDebug(dlLink)
            self.download(dlLink)

    def getQuality(self, quality, data):
        link = re.search('"' + quality + '":"(http:[^<>"\']+)"', data)
        if link is None:
            return link
        else:
            return link.group(1).replace('\\','')
