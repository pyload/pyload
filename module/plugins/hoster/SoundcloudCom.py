# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.common.json_layer import json_loads


class SoundcloudCom(SimpleHoster):
    __name__    = "SoundcloudCom"
    __type__    = "hoster"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?soundcloud\.com/[\w-]+/[\w-]+'
    __config__  = [("use_premium", "bool"        , "Use premium account if available", True    ),
                   ("quality"    , "Lower;Higher", "Quality"                         , "Higher")]

    __description__ = """SoundCloud.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'title" content="(?P<N>.+?)"'
    OFFLINE_PATTERN = r'<title>"SoundCloud - Hear the world’s sounds"</title>'


    def handle_free(self, pyfile):
        try:
            song_id = re.search(r'sounds:(\d+)"', self.html).group(1)

        except Exception:
            self.error(_("Could not find song id"))

        try:
            client_id = re.search(r'"clientID":"(.+?)"', self.html).group(1)

        except Exception:
            client_id = "b45b1aa10f1ac2941910a7f0d10f8e28"

        #: Url to retrieve the actual song url
        streams = json_loads(self.load("https://api.soundcloud.com/tracks/%s/streams" % song_id,
                             get={'client_id': client_id}))

        regex = re.compile(r'[^\d]')
        http_streams = sorted([(key, value) for key, value in streams.items() if key.startswith('http_')],
                              key=lambda t: regex.sub(t[0], ''),
                              reverse=True)

        self.log_debug("Streams found: %s" % (http_streams or "None"))

        if http_streams:
            stream_name, self.link = http_streams[0 if self.get_config('quality') == "Higher" else -1]
            pyfile.name += '.' + stream_name.split('_')[1].lower()


getInfo = create_getInfo(SoundcloudCom)
