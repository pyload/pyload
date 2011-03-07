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
    __config__ = [ ("quality", "str" , "Quality Setting", "hd") ]
    __description__ = """Youtube.com Video Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")
   
    def process(self, pyfile):
        html = self.load(pyfile.url)

        if re.search(r"(.*eine fehlerhafte Video-ID\.)", html) is not None:
            self.offline()
       
        videoId = pyfile.url.split("v=")[1].split("&")[0]
        videoHash = re.search(r'&amp;t=(.+?)&', html).group(1)
       
       
        file_name_pattern = '<meta name="title" content="(.+?)">'
        is_hd_pattern = r"'IS_HD_AVAILABLE': (false|true)"
        file_suffix = ".flv"
        is_hd = re.search(is_hd_pattern, html).group(1)
        hd_available = (is_hd == "true")
       
        if self.getConf("quality") == "hd" or self.getConf("quality") == "hq":
            file_suffix = ".mp4"

        name = (re.search(file_name_pattern, html).group(1).replace("/", "") + file_suffix).decode("utf8")
        pyfile.name = name #.replace("&amp;", "&").replace("ö", "oe").replace("ä", "ae").replace("ü", "ue")       

        file_url = ""
        desired_fmt="18"
        if self.getConf("quality") == "sd":
            desired_fmt = "6"
        elif self.getConf("quality") == "hd" and hd_available:
            desired_fmt = "22"
        elif self.getConf("quality") == "fullhd" and hd_available:
            desired_fmt = "37"

        fmt_pattern = 'fmt_url_map=(.+?)&'
        fmt_url_map = re.search(fmt_pattern, html).group(1)
        links = urllib.unquote(fmt_url_map).split(",")
        for i in range(1, len(links)):
            fmt = links[i].split("|")[0] 
            if fmt == desired_fmt:
                file_url = links[i].split("|")[1]

        if file_url == "":
            for i in range(1, len(links)):
                fmt = links[i].split("|")[0]   
                if fmt == "5":
                    file_url = links[i].split("|")[1]


        self.download(file_url)
