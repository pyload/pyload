# -*- coding: utf-8 -*-

import hashlib
import os
import time
import urlparse

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


def get_api_password(episode):
    api_key = "fb5f58a820353bd7095de526253c14fd"

    timestamp = int(round(time.time() / 24 / 3600))
    api_pass = api_key + "/episode/" + episode + str(timestamp)

    m = hashlib.md5(api_pass)

    return m.hexdigest()


def get_all_link(data, container):
    videos = []

    for i in range(0, len(data["video_qualities"])):
        if container == "webm" and len(
                data["video_qualities"][i]["formats"]) != 1:
            videos.append(data["video_qualities"][i]["formats"][1]["source"])

        else:
            videos.append(data["video_qualities"][i]["formats"][0]["source"])

    return videos


def get_link_quality(videos, quality):
    quality_index = ["144p", "240p", "360p", "480p", "720p", "1080p"]
    quality = quality_index.index(quality)

    link = None
    while quality >= 0:
        if len(videos) >= quality + 1:
            link = videos[quality]
            break

        else:
            quality -= 1

    return link


class StreamCz(SimpleHoster):
    __name__ = "StreamCz"
    __type__ = "hoster"
    __version__ = "0.41"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?stream\.cz/[^/]+/(?P<EP>\d+).+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("quality", "144p;240p;360p;480p;720p;1080p", "Quality", "720p"),
                  ("container", "mp4;webm", "Container", "mp4"), ]

    __description__ = """Stream.cz hoster plugin"""
    __authors__ = [("ondrej", "git@ondrej.it")]

    def setup(self):
        self.resume_download = True
        self.multiDL = True

    def process(self, pyfile):
        episode = self.info['pattern']['EP']
        api_password = get_api_password(episode)

        api_url = urlparse.urljoin(
            "https://www.stream.cz/API/episode/", episode)
        self.req.putHeader("Api-Password", api_password)
        resp = self.load(api_url)

        data = json.loads(resp)

        quality = self.config.get("quality")
        container = self.config.get("container")

        videos = get_all_link(data, container)
        link = get_link_quality(videos, quality)

        if link:
            link_name, container = os.path.splitext(link)
            self.pyfile.name = data["name"] + container

            self.log_info(_("Downloading file..."))
            self.download(link)
