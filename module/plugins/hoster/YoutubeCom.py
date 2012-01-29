#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib import unquote

from module.utils import html_unescape
from module.plugins.Hoster import Hoster

class YoutubeCom(Hoster):
    __name__ = "YoutubeCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?(de\.)?\youtube\.com/watch\?v=.*"
    __version__ = "0.25"
    __config__ = [("quality", "sd;hd;fullhd", "Quality Setting", "hd"),
        ("fmt", "int", "FMT Number 0-45", 0),
        (".mp4", "bool", "Allow .mp4", True),
        (".flv", "bool", "Allow .flv", True),
        (".webm", "bool", "Allow .webm", False),
        (".3gp", "bool", "Allow .3gp", False)]
    __description__ = """Youtube.com Video Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    # name, width, height, quality ranking
    formats = {17: (".3gp", 176, 144, 0),
               5: (".flv", 400, 240, 1),
               18: (".mp4", 480, 360, 2),
               43: (".webm", 640, 360, 3),
               34: (".flv", 640, 360, 4),
               44: (".webm", 854, 480, 5),
               35: (".flv", 854, 480, 6),
               45: (".webm", 1280, 720, 7),
               22: (".mp4", 1280, 720, 8),
               37: (".mp4", 1920, 1080, 9),
               38: (".mp4", 4096, 3072, 10),
               }


    def process(self, pyfile):
        html = self.load(pyfile.url, decode=True)

        if "watch-player-unavailable" in html:
            self.offline()

        if "We have been receiving a large volume of requests from your network." in html:
            self.tempOffline()

        #videoId = pyfile.url.split("v=")[1].split("&")[0]
        #videoHash = re.search(r'&amp;t=(.+?)&', html).group(1)

        file_name_pattern = '<meta name="title" content="(.+?)">'

        quality = self.getConf("quality")
        desired_fmt = 18

        if quality == "sd":
            desired_fmt = 18
        elif quality == "hd":
            desired_fmt = 22
        elif quality == "fullhd":
            desired_fmt = 37

        if self.getConfig("fmt"):
            desired_fmt = self.getConf("fmt")

        flashvars = re.search(r'flashvars=\\"(.*?)\\"', html)
        flashvars = unquote(flashvars.group(1))

        fmts = re.findall(r'url=(.*?)%3B.*?itag=(\d+)', flashvars)
        fmt_dict = {}
        for url, fmt in fmts:
            fmt = int(fmt)
            fmt_dict[fmt] = unquote(url)

        
        self.logDebug("Found links: %s" % fmt_dict)
        for fmt in fmt_dict.keys():
            if fmt not in self.formats:
                self.logDebug("FMT not supported: %s" % fmt)
                del fmt_dict[fmt]

        allowed = lambda x: self.getConfig(self.formats[x][0])
        sel = lambda x: self.formats[x][3] #select quality index
        comp = lambda x, y: abs(sel(x) - sel(y))

        #return fmt nearest to quali index
        fmt = reduce(lambda x, y: x if comp(x, desired_fmt) <= comp(y, desired_fmt) and
                                       sel(x) > sel(y) and
                                       allowed(x) else y, fmt_dict.keys())

        self.logDebug("Choose fmt: %s" % fmt)

        file_suffix = ".flv"
        if fmt in self.formats:
            file_suffix = self.formats[fmt][0]
        name = re.search(file_name_pattern, html).group(1).replace("/", "") + file_suffix
        pyfile.name = html_unescape(name)

        self.download(fmt_dict[fmt])
