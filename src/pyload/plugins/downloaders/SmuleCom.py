# -*- coding: utf-8 -*-
import re

from pyload.core.utils.misc import eval_js

from ..base.simple_downloader import SimpleDownloader


class SmuleCom(SimpleDownloader):
    __name__ = "SmuleCom"
    __type__ = "downloader"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?smule\.com/recording/.+"

    __description__ = """SmuleCom downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("igel", None), ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    MEDIA_URL_PATTERN = r'initPlayer\(.+?["\']video_media_url["\']:["\'](.+?)["\']'
    JS_HEADER_PATTERN = r"(?P<decoder>function \w+\(\w+\){.+?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\+.+?}).+?;(?P<initvars>var r=.+?;)"
    JS_PROCESS_PATTERN = r"processRecording\s*=\s*function.+?}"
    # all interesting parts of the javascript function occur before the first
    # occurance of this word
    JS_SPLIT_WORD = r"EXIF"
    NAME_PATTERN = r'initPlayer\(.+?["\']title["\']:["\'](?P<N>.+?)["\']'
    COMMUNITY_JS_PATTERN = r'<script.+?src=["\']/*(\w[^"\']*community.+?js)["\']'
    OFFLINE_PATTERN = r"Page Not Found"

    @classmethod
    def get_info(cls, url="", html=""):
        info = SimpleDownloader.get_info(url, html)
        # Unfortunately, NAME_PATTERN does not include file extension so we blindly add '.mp4' as an extension.
        # (hopefully all links are '.mp4' files)
        if "name" in info:
            info["name"] += ".mp4"

        return info

    def handle_free(self, pyfile):
        # step 1: get essential information: the media URL and the javascript
        # translating the URL
        m = re.search(self.MEDIA_URL_PATTERN, self.data)
        if m is None:
            self.fail(self._("Could not find any media URLs"))

        encoded_media_url = m.group(1)
        self.log_debug(f"Found encoded media URL: {encoded_media_url}")

        m = re.search(self.COMMUNITY_JS_PATTERN, self.data)
        if m is None:
            self.fail(self._("Could not find necessary javascript script to load"))

        community_js_url = m.group(1)
        self.log_debug(f"Found community js at {community_js_url}")

        community_js_code = self.load(community_js_url)

        # step 2: from the js code, parse the necessary parts: the decoder function and the headers
        # as the jscript is fairly long, we'll split it to make parsing easier
        community_js_code = community_js_code.partition(self.JS_SPLIT_WORD)[0]

        m = re.search(self.JS_HEADER_PATTERN, community_js_code)
        if m is None:
            self.fail(self._("Could not parse the necessary parts off the javascript"))

        decoder_function = m.group("decoder")
        initialization = m.group("initvars")

        m = re.search(self.JS_PROCESS_PATTERN, community_js_code)
        if m is None:
            self.fail(
                self._("Could not parse the processing function off the javascript")
            )

        process_function = m.group(0)

        new_js_code = (
            decoder_function
            + "; "
            + initialization
            + "; var "
            + process_function
            + '; processRecording("'
            + encoded_media_url
            + '");'
        )

        self.log_debug(f"Running js script: {new_js_code}")
        js_result = eval_js(new_js_code)
        self.log_debug(f"Result is: {js_result}")

        self.link = js_result
