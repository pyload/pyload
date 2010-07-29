#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class YoutubeCom(Hoster):
    __name__ = "YoutubeCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?(de\.)?\youtube\.com/watch\?v=.*"
    __version__ = "0.2"
    __config__ = [ ("int", "quality" , "Quality Setting", "hd;lq"),
                   ("int", "config", "Config Settings" , "default" ) ]
    __description__ = """Youtube.com Video Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.read_config()
        self.hd_available = False

    def download_html(self):
        url = self.parent.url
        self.html = self.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()

        videoId = self.parent.url.split("v=")[1].split("&")[0]
        videoHash = re.search(r'&t=(.+?)&', self.html).group(1)
        quality = ""
        if self.config['quality'] == "sd":
            quality = "&fmt=6"
        elif self.config['quality'] == "hd" and self.hd_available:
            quality = "&fmt=22"
        else:
            quality = "&fmt=18"
        file_url = 'http://youtube.com/get_video?video_id=' + videoId + '&t=' + videoHash + quality
        return file_url
    
    def verify_config(self):
        q = self.get_config("quality")
        if not (q == "hq" or q == "hd" or q == "sd"):
            self.config["quality"] = "hd"
        hq = self.get_config("high_quality")
        if hq:
            self.remove_config("high_quality")
        self.set_config()

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        file_name_pattern = '<meta name="title" content="(.+?)">'
        is_hd_pattern = r"'IS_HD_AVAILABLE': (false|true)"
        file_suffix = ".flv"
        is_hd = re.search(is_hd_pattern, self.html).group(1)
        self.hd_available = (is_hd == "true")
        if self.config['quality'] == "hd" or self.config['quality'] == "hq":
            file_suffix = ".mp4"
        name = re.search(file_name_pattern, self.html).group(1).replace("/", "") + file_suffix
        
        name = name.replace("&amp;", "&").replace("ö", "oe").replace("ä", "ae").replace("ü", "ue")
        return name

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"(.*eine fehlerhafte Video-ID\.)", self.html) != None:
            return False
        else:
            return True
