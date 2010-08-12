#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
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
                        
        if re.search(r"(.*eine fehlerhafte Video-ID\.)", html) != None:
            self.offline()
        
        videoId = pyfile.url.split("v=")[1].split("&")[0]
        videoHash = re.search(r'&t=(.+?)&', html).group(1)
        
        
        file_name_pattern = '<meta name="title" content="(.+?)">'
        is_hd_pattern = r"'IS_HD_AVAILABLE': (false|true)"
        file_suffix = ".flv"
        is_hd = re.search(is_hd_pattern, html).group(1)
        hd_available = (is_hd == "true")
        
        if self.getConf("quality") == "hd" or self.getConf("quality") == "hq":
            file_suffix = ".mp4"
        name = re.search(file_name_pattern, html).group(1).replace("/", "") + file_suffix
        
        pyfile.name = name.replace("&amp;", "&").replace("ö", "oe").replace("ä", "ae").replace("ü", "ue")        

        if self.getConf("quality") == "sd":
            quality = "&fmt=6"
        elif self.getConf("quality") == "hd" and hd_available:
            quality = "&fmt=22"
        else:
            quality = "&fmt=18"
            
        file_url = 'http://youtube.com/get_video?video_id=' + videoId + '&t=' + videoHash + quality + "&asv=2"

        self.download(file_url)
