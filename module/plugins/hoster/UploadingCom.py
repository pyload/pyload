# -*- coding: utf-8 -*-

import re

import pycurl

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import encode, json, timestamp


class UploadingCom(SimpleHoster):
    __name__    = "UploadingCom"
    __type__    = "hoster"
    __version__ = "0.48"
    __status__  = "broken"

    __pattern__ = r'http://(?:www\.)?uploading\.com/files/(?:get/)?(?P<ID>\w+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Uploading.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'id="file_title">(?P<N>.+?)</'
    SIZE_PATTERN = r'size tip_container">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r'(Page|file) not found'

    COOKIES = [("uploading.com", "lang", "1"),
               (".uploading.com", "language", "1"),
               (".uploading.com", "setlang", "en"),
               (".uploading.com", "_lang", "en")]


    def process(self, pyfile):
        if not "/get/" in pyfile.url:
            pyfile.url = pyfile.url.replace("/files", "/files/get")

        self.data = self.load(pyfile.url)
        self.get_fileInfo()

        if self.premium:
            self.handle_premium(pyfile)
        else:
            self.handle_free(pyfile)


    def handle_premium(self, pyfile):
        postData = {'action': 'get_link',
                    'code'  : self.info['pattern']['ID'],
                    'pass'  : 'undefined'}

        self.data = self.load('http://uploading.com/files/get/?JsHttpRequest=%d-xml' % timestamp(), post=postData)
        url = re.search(r'"link"\s*:\s*"(.*?)"', self.data)
        if url:
            self.link = url.group(1).replace("\\/", "/")

        raise Exception("Plugin defect")


    def handle_free(self, pyfile):
        m = re.search('<h2>((Daily )?Download Limit)</h2>', self.data)
        if m is not None:
            pyfile.error = encode(m.group(1))
            self.log_warning(pyfile.error)
            self.retry(6, (6 * 60 if m.group(2) else 15) * 60, pyfile.error)

        ajax_url = "http://uploading.com/files/get/?ajax"
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = pyfile.url

        html = self.load(ajax_url,
                         post={'action': 'second_page',
                               'code'  : self.info['pattern']['ID']})
        res = json.loads(html)

        if 'answer' in res and 'wait_time' in res['answer']:
            wait_time = int(res['answer']['wait_time'])
            self.log_info(_("Waiting %d seconds") % wait_time)
            self.wait(wait_time)
        else:
            self.error(_("No AJAX/WAIT"))

        html = self.load(ajax_url,
                         post={'action': 'get_link',
                               'code'  : self.info['pattern']['ID'],
                               'pass'  : 'false'})
        res = json.loads(html)

        if 'answer' in res and 'link' in res['answer']:
            url = res['answer']['link']
        else:
            self.error(_("No AJAX/URL"))

        self.data = self.load(url)
        m = re.search(r'<form id="file_form" action="(.*?)"', self.data)
        if m is not None:
            url = m.group(1)
        else:
            self.error(_("No URL"))

        self.link = url
