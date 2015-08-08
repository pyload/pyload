# -*- coding: utf-8 -*-

import os
import re
import subprocess
import urllib

from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.Plugin import replace_patterns
from module.utils import html_unescape


def which(program):
    """
    Works exactly like the unix command which
    Courtesy of http://stackoverflow.com/a/377028/675646
    """
    isExe = lambda x: os.path.isfile(x) and os.access(x, os.X_OK)

    fpath, fname = os.path.split(program)

    if fpath:
        if isExe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if isExe(exe_file):
                return exe_file


class YoutubeCom(Hoster):
    __name__    = "YoutubeCom"
    __type__    = "hoster"
    __version__ = "0.44"
    __status__  = "testing"

    __pattern__ = r'https?://(?:[^/]*\.)?(youtube\.com|youtu\.be)/watch\?(?:.*&)?v=.+'
    __config__  = [("quality", "sd;hd;fullhd;240p;360p;480p;720p;1080p;3072p", "Quality Setting"             , "hd" ),
                   ("fmt"    , "int"                                         , "FMT/ITAG Number (0 for auto)", 0    ),
                   (".mp4"   , "bool"                                        , "Allow .mp4"                  , True ),
                   (".flv"   , "bool"                                        , "Allow .flv"                  , True ),
                   (".webm"  , "bool"                                        , "Allow .webm"                 , False),
                   (".3gp"   , "bool"                                        , "Allow .3gp"                  , False),
                   ("3d"     , "bool"                                        , "Prefer 3D"                   , False)]

    __description__ = """Youtube.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    URL_REPLACEMENTS = [(r'youtu\.be/', 'youtube.com/')]

    #: Invalid characters that must be removed from the file name
    invalidChars = u'\u2605:?><"|\\'

    #: name, width, height, quality ranking, 3D
    formats = {5  : (".flv" , 400 , 240 , 1 , False),
               6  : (".flv" , 640 , 400 , 4 , False),
               17 : (".3gp" , 176 , 144 , 0 , False),
               18 : (".mp4" , 480 , 360 , 2 , False),
               22 : (".mp4" , 1280, 720 , 8 , False),
               43 : (".webm", 640 , 360 , 3 , False),
               34 : (".flv" , 640 , 360 , 4 , False),
               35 : (".flv" , 854 , 480 , 6 , False),
               36 : (".3gp" , 400 , 240 , 1 , False),
               37 : (".mp4" , 1920, 1080, 9 , False),
               38 : (".mp4" , 4096, 3072, 10, False),
               44 : (".webm", 854 , 480 , 5 , False),
               45 : (".webm", 1280, 720 , 7 , False),
               46 : (".webm", 1920, 1080, 9 , False),
               82 : (".mp4" , 640 , 360 , 3 , True ),
               83 : (".mp4" , 400 , 240 , 1 , True ),
               84 : (".mp4" , 1280, 720 , 8 , True ),
               85 : (".mp4" , 1920, 1080, 9 , True ),
               100: (".webm", 640 , 360 , 3 , True ),
               101: (".webm", 640 , 360 , 4 , True ),
               102: (".webm", 1280, 720 , 8 , True )}


    def setup(self):
        self.resume_download = True
        self.multiDL        = True


    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)
        html       = self.load(pyfile.url)

        if re.search(r'<div id="player-unavailable" class="\s*player-width player-height\s*">', html):
            self.offline()

        if "We have been receiving a large volume of requests from your network." in html:
            self.temp_offline()

        #: Get config
        use3d = self.get_config('3d')

        if use3d:
            quality = {'sd': 82, 'hd': 84, 'fullhd': 85, '240p': 83, '360p': 82,
                       '480p': 82, '720p': 84, '1080p': 85, '3072p': 85}
        else:
            quality = {'sd': 18, 'hd': 22, 'fullhd': 37, '240p': 5, '360p': 18,
                       '480p': 35, '720p': 22, '1080p': 37, '3072p': 38}

        desired_fmt = self.get_config('fmt')

        if not desired_fmt:
            desired_fmt = quality.get(self.get_config('quality'), 18)

        elif desired_fmt not in self.formats:
            self.log_warning(_("FMT %d unknown, using default") % desired_fmt)
            desired_fmt = 0

        #: Parse available streams
        streams = re.search(r'"url_encoded_fmt_stream_map":"(.+?)",', html).group(1)
        streams = [x.split('\u0026') for x in streams.split(',')]
        streams = [dict((y.split('=', 1)) for y in x) for x in streams]
        streams = [(int(x['itag']), urllib.unquote(x['url'])) for x in streams]

        # self.log_debug("Found links: %s" % streams)

        self.log_debug("AVAILABLE STREAMS: %s" % [x[0] for x in streams])

        #: Build dictionary of supported itags (3D/2D)
        allowed = lambda x: self.get_config(self.formats[x][0])
        streams = [x for x in streams if x[0] in self.formats and allowed(x[0])]

        if not streams:
            self.fail(_("No available stream meets your preferences"))

        fmt_dict = dict([x for x in streams if self.formats[x[0]][4] is use3d] or streams)

        self.log_debug("DESIRED STREAM: ITAG:%d (%s) %sfound, %sallowed" %
                      (desired_fmt, "%s %dx%d Q:%d 3D:%s" % self.formats[desired_fmt],
                       "" if desired_fmt in fmt_dict else "NOT ", "" if allowed(desired_fmt) else "NOT "))

        #: Return fmt nearest to quality index
        if desired_fmt in fmt_dict and allowed(desired_fmt):
            fmt = desired_fmt
        else:
            sel  = lambda x: self.formats[x][3]  #: Select quality index
            comp = lambda x, y: abs(sel(x) - sel(y))

            self.log_debug("Choosing nearest fmt: %s" % [(x, allowed(x), comp(x, desired_fmt)) for x in fmt_dict.keys()])

            fmt = reduce(lambda x, y: x if comp(x, desired_fmt) <= comp(y, desired_fmt) and
                         sel(x) > sel(y) else y, fmt_dict.keys())

        self.log_debug("Chosen fmt: %s" % fmt)

        url = fmt_dict[fmt]

        self.log_debug("URL: %s" % url)

        #: Set file name
        file_suffix = self.formats[fmt][0] if fmt in self.formats else ".flv"
        file_name_pattern = '<meta name="title" content="(.+?)">'
        name = re.search(file_name_pattern, html).group(1).replace("/", "")

        #: Cleaning invalid characters from the file name
        name = name.encode('ascii', 'replace')
        for c in self.invalid_chars:
            name = name.replace(c, '_')

        pyfile.name = html_unescape(name)

        time = re.search(r"t=((\d+)m)?(\d+)s", pyfile.url)
        ffmpeg = which("ffmpeg")
        if ffmpeg and time:
            m, s = time.groups()[1:]
            if m is None:
                m = "0"

            pyfile.name += " (starting at %s:%s)" % (m, s)

        pyfile.name += file_suffix
        filename     = self.download(url)

        if ffmpeg and time:
            inputfile = filename + "_"
            os.rename(filename, inputfile)

            subprocess.call([
                ffmpeg,
                "-ss", "00:%s:%s" % (m, s),
                "-i", inputfile,
                "-vcodec", "copy",
                "-acodec", "copy",
                filename])

            os.remove(inputfile)
