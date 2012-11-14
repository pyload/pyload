#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib import unquote

from module.utils import html_unescape
from module.plugins.Hoster import Hoster

class YoutubeCom(Hoster):
    __name__ = "YoutubeCom"
    __type__ = "hoster"
    __pattern__ = r"(http|https)://(www\.)?(de\.)?\youtube\.com/watch\?v=.*"
    __version__ = "0.28"
    __config__ = [("quality", "sd;hd;fullhd;240p;360p;480p;720p;1080p;3072p", "Quality Setting", "hd"),
        ("fmt", "int", "FMT/ITAG Number (5-102, 0 for auto)", 0),
        (".mp4", "bool", "Allow .mp4", True),
        (".flv", "bool", "Allow .flv", True),
        (".webm", "bool", "Allow .webm", False),
        (".3gp", "bool", "Allow .3gp", False),
        ("3d", "bool", "Prefer 3D", False)]
    __description__ = """Youtube.com Video Download Hoster"""
    __author_name__ = ("spoob", "zoidberg")
    __author_mail__ = ("spoob@pyload.org", "zoidberg@mujmail.cz")

    # name, width, height, quality ranking, 3D
    formats = {5: (".flv", 400, 240, 1, False), 
                6: (".flv", 640, 400, 4, False),
               17: (".3gp", 176, 144, 0, False), 
               18: (".mp4", 480, 360, 2, False),
               22: (".mp4", 1280, 720, 8, False),
               43: (".webm", 640, 360, 3, False),
               34: (".flv", 640, 360, 4, False),
               35: (".flv", 854, 480, 6, False),
                36: (".3gp", 400, 240, 1, False),
               37: (".mp4", 1920, 1080, 9, False),
               38: (".mp4", 4096, 3072, 10, False),
               44: (".webm", 854, 480, 5, False),
               45: (".webm", 1280, 720, 7, False), 
                46: (".webm", 1920, 1080, 9, False),
                82: (".mp4", 640, 360, 3, True),
                83: (".mp4", 400, 240, 1, True),
                84: (".mp4", 1280, 720, 8, True),
                85: (".mp4", 1920, 1080, 9, True),
                100: (".webm", 640, 360, 3, True),
                101: (".webm", 640, 360, 4, True),
                102: (".webm", 1280, 720, 8, True)
               }

    def setup(self):
        self.resumeDownload = self.multiDL = True

    def process(self, pyfile):
        html = self.load(pyfile.url, decode=True)

        if "watch-player-unavailable" in html:
            self.offline()

        if "We have been receiving a large volume of requests from your network." in html:
            self.tempOffline()
        
        #get config
        use3d = self.getConf("3d")
        if use3d:
            quality = {"sd":82,"hd":84,"fullhd":85,"240p":83,"360p":82,"480p":82,"720p":84,"1080p":85,"3072p":85} 
        else:
            quality = {"sd":18,"hd":22,"fullhd":37,"240p":5,"360p":18,"480p":35,"720p":22,"1080p":37,"3072p":38} 
        desired_fmt = self.getConf("fmt")
        if desired_fmt and desired_fmt not in formats:
            self.logWarning("FMT %d unknown - using default." % desired_fmt) 
            desired_fmt = 0 
        if not desired_fmt:
            desired_fmt = quality.get(self.getConf("quality"), 18)        
        
        #parse available streams
        streams = unquote(re.search(r'url_encoded_fmt_stream_map=(.*?);', html).group(1))
        streams = [x.split('&') for x in streams.split(',')]
        streams = [dict((y.split('=')) for y in x) for x in streams]
        streams = [(int(x['itag']), "%s&signature=%s" % (unquote(x['url']), x['sig'])) for x in streams]                         
        #self.logDebug("Found links: %s" % streams) 
        self.logDebug("AVAILABLE STREAMS: %s" % [x[0] for x in streams])                    
        
        #build dictionary of supported itags (3D/2D)
        allowed = lambda x: self.getConfig(self.formats[x][0])        
        streams = [x for x in streams if x[0] in self.formats and allowed(x[0])]
        if not streams:
            self.fail("No available stream meets your preferences")
        fmt_dict = dict([x for x in streams if self.formats[x[0]][4] == use3d] or streams)              
                
        self.logDebug("DESIRED STREAM: ITAG:%d (%s) %sfound, %sallowed" % 
                          (desired_fmt, 
                           "%s %dx%d Q:%d 3D:%s" % self.formats[desired_fmt],
                           "" if desired_fmt in fmt_dict else "NOT ", 
                           "" if allowed(desired_fmt) else "NOT ")
                      )        

        #return fmt nearest to quality index        
        if desired_fmt in fmt_dict and allowed(desired_fmt):
            fmt = desired_fmt
        else:
            sel = lambda x: self.formats[x][3] #select quality index
            comp = lambda x, y: abs(sel(x) - sel(y))
        
            self.logDebug("Choosing nearest fmt: %s" % [(x, allowed(x), comp(x, desired_fmt)) for x in fmt_dict.keys()])
            fmt = reduce(lambda x, y: x if comp(x, desired_fmt) <= comp(y, desired_fmt) and
                                       sel(x) > sel(y) else y, fmt_dict.keys())

        self.logDebug("Chosen fmt: %s" % fmt)
        url = fmt_dict[fmt]
        self.logDebug("URL: %s" % url)

        #set file name        
        file_suffix = self.formats[fmt][0] if fmt in self.formats else ".flv"
        file_name_pattern = '<meta name="title" content="(.+?)">'
        name = re.search(file_name_pattern, html).group(1).replace("/", "") + file_suffix
        pyfile.name = html_unescape(name)
        
        self.download(url)