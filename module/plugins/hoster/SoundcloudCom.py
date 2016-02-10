# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import json


class SoundcloudCom(SimpleHoster):
    __name__    = "SoundcloudCom"
    __type__    = "hoster"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?soundcloud\.com/[\w\-]+/[\w\-]+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """SoundCloud.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de"     , "nitzo2001[AT]yahoo[DOT]com")]


    NAME_PATTERN    = r'title" content="(?P<N>.+?)"'
    OFFLINE_PATTERN = r'<title>"SoundCloud - Hear the world’s sounds"</title>'


    def handle_free(self, pyfile):
        try:
            song_id = re.search(r'sounds:(\d+)"', self.data).group(1)

        except Exception:
            self.error(_("Could not find song id"))

        try:
            client_id = re.search(r'"clientID":"(.+?)"', self.data).group(1)

        except Exception:
            client_id = "02gUJC0hH2ct1EGOcYXQIzRFU91c72Ea"

        #: Url to retrieve the actual song url
        html = self.load("https://api.soundcloud.com/tracks/%s/streams" % song_id,
                         get={'client_id': client_id})
        streams = json.loads(html)

        regex = re.compile(r'[^\d]')
        http_streams = sorted([(key, value) for key, value in streams.items() if key.startswith('http_')],
                              key=lambda t: regex.sub(t[0], ''),
                              reverse=True)

        self.log_debug("Streams found: %s" % (http_streams or "None"))

        if http_streams:
            stream_name, self.link = http_streams[0 if self.config.get('quality') == "Higher" else -1]
            pyfile.name += '.' + stream_name.split('_')[1].lower()
