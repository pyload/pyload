# -*- coding: utf-8 -*-

import re

from module.common.JsEngine import JsEngine
from module.plugins.internal.SimpleHoster import SimpleHoster


class SmuleCom(SimpleHoster):
    __name__    = "SmuleCom"
    __type__    = "hoster"
    __version__ = "0.01"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?smule\.com'

    __description__ = """SmuleCom hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "")]


    MEDIA_URL_PATTERN       = r"initPlayer\(.*?[\"']video_media_url[\"']:[\"'](.*?)[\"']"
    JS_HEADER_PATTERN      = r"(?P<decoder>function \w+\(\w+\){.*?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\+.*?}).*?;(?P<initvars>var r=.*?;)"
    JS_PROCESS_PATTERN      = r"processRecording\s*=\s*function.*?}"
    JS_SPLIT_WORD           = r'EXIF' # all interesting parts of the javascript function occur before the first occurance of this word
    NAME_PATTERN            = r"initPlayer\(.*?[\"']title[\"']:[\"'](?P<N>.*?)[\"']"
    COMMUNITY_JS_PATTERN    = r"<script.*?src=[\"']/*(\w[^\"']*community.*?js)[\"']"
    OFFLINE_PATTERN         = r'Page Not Found'


    def handle_free(self, pyfile):
        # step 1: get essential information: the media URL and the javascript translating the URL
        m = re.search(self.MEDIA_URL_PATTERN, self.data)
        if not m:
            self.fail(_('Could not find any media URLs'))
        encoded_media_url = m.group(1)
        self.log_debug('found encoded media URL: %s' % encoded_media_url)
       
        m = re.search(self.COMMUNITY_JS_PATTERN, self.data)
        if not m:
            self.fail(_('Could not find necessary javascript script to load'))
        community_js_url = m.group(1)
        self.log_debug('found community js at %s' % community_js_url)

        community_js_code = self.load(community_js_url)
        
        # step 2: from the js code, parse the necessary parts: the decoder function and the headers
        # as the jscript is fairly long, we'll split it to make parsing easier
        if self.JS_SPLIT_WORD:
            community_js_code = community_js_code.partition(self.JS_SPLIT_WORD)[0]

        m = re.search(self.JS_HEADER_PATTERN, community_js_code)
        if not m:
            self.fail(_('Could not parse the necessary parts off the javascript'))
        decoder_function = m.group('decoder')
        initialization = m.group('initvars')
        
        m = re.search(self.JS_PROCESS_PATTERN, community_js_code)
        if not m:
            self.fail(_('Could not parse the processing function off the javascript'))
        process_function = m.group(0)

        # step 3: assemble the new js code
        js = JsEngine()
        new_js_code = decoder_function + '; ' + initialization + '; var ' + process_function + '; ' + js.print_command() + '(processRecording("' + encoded_media_url + '"));'
        # self.log_debug('running js script: %s' % new_js_code)
        js_result = js.eval_raw(new_js_code)
        # self.log_debug('result is: %s' % js_result)
        self.link = js_result

