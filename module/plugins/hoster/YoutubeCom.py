#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster

class YoutubeCom(Hoster):
    __name__ = "YoutubeCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?(de\.)?\youtube\.com/watch\?v=.*"
    __version__ = "0.2"
    __config__ = [("quality", "sd;hd;fullhd", "Quality Setting", "hd"),
                  ("fmt", "int", "FMT Number 0-45", 0),
                  (".mp4", "bool", "Allow .mp4", True),
                  (".flv", "bool", "Allow .flv", True),
                  (".webm", "bool", "Allow .webm", False),
                  (".3gp", "bool", "Allow .3gp", False)]
    __description__ = """Youtube.com Video Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    formats = {5: (".flv", 400, 240),
               34: (".flv", 640, 360),
               35: (".flv", 854, 480),
               18: (".mp4", 480, 360),
               22: (".mp4", 1280, 720),
               37: (".mp4", 1920, 1080),
               38: (".mp4", 4096, 3072),
               43: (".webm", 640, 360),
               45: (".webm", 1280, 720),
               17: (".3gp", 176, 144)
    }

    quality_sequence = (38, 37, 22, 45, 35, 34, 43, 18, 5, 17)

    def process(self, pyfile):
        html = self.load(pyfile.url, decode=True)

        if "watch-player-unavailable" in html:
            self.offline()

        videoId = pyfile.url.split("v=")[1].split("&")[0]
        videoHash = re.search(r'&amp;t=(.+?)&', html).group(1)

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

        fmt_pattern = 'fmt_url_map=(.+?)&'
        fmt_url_map = re.search(fmt_pattern, html).group(1)
        links = urllib.unquote(fmt_url_map).split(",")

        fmt_dict = {}
        for link in links:
            fmt = link.split("|")[0]
            try:
                fmt = int(fmt)
            except Exception:
                continue

            fmt_dict[fmt] = link.split("|")[1]

        self.logDebug("Found links: %s" % fmt_dict)

        self.logDebug("Desired fmt: %s" % desired_fmt)
         
        for testfmt in self.quality_sequence[self.quality_sequence.index(desired_fmt):-1]:
            if testfmt in fmt_dict and self.getConfig(self.formats[testfmt][0]):
                fmt=testfmt
                break

        self.logDebug("Choose fmt: %s" % fmt)

        file_suffix = ".flv"
        if fmt in self.formats:
            file_suffix = self.formats[fmt][0]
        name = re.search(file_name_pattern, html).group(1).replace("/", "") + file_suffix
        pyfile.name = name #.replace("&amp;", "&").replace("ö", "oe").replace("ä", "ae").replace("ü", "ue")       

        self.download(fmt_dict[fmt])
