# -*- coding: utf-8 -*-

import re
import urllib

from module.common.json_layer import json_loads
from module.plugins.internal.Hoster import Hoster


def clean_json(json_expr):
    json_expr = re.sub('[\n\r]', '', json_expr)
    json_expr = re.sub(' +', '', json_expr)
    json_expr = re.sub('\'', '"', json_expr)

    return json_expr


class XHamsterCom(Hoster):
    __name__    = "XHamsterCom"
    __type__    = "hoster"
    __version__ = "0.14"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?xhamster\.com/movies/.+'
    __config__  = [("type", ".mp4;.flv", "Preferred type", ".mp4")]

    __description__ = """XHamster.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = []


    def process(self, pyfile):
        self.pyfile = pyfile

        if not self.file_exists():
            self.offline()

        if self.get_config('type'):
            self.desired_fmt = self.get_config('type')

        pyfile.name = self.get_file_name() + self.desired_fmt
        self.download(self.get_file_url())


    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)


    def get_file_url(self):
        """
        Returns the absolute downloadable filepath
        """
        if not self.html:
            self.download_html()

        flashvar_pattern = re.compile('flashvars = ({.*?});', re.S)
        json_flashvar = flashvar_pattern.search(self.html)

        if not json_flashvar:
            self.error(_("flashvar not found"))

        j = clean_json(json_flashvar.group(1))
        flashvars = json_loads(j)

        if flashvars['srv']:
            srv_url = flashvars['srv'] + '/'
        else:
            self.error(_("srv_url not found"))

        if flashvars['url_mode']:
            url_mode = flashvars['url_mode']


        else:
            self.error(_("url_mode not found"))

        if self.desired_fmt == ".mp4":
            file_url = re.search(r"<a href=\"" + srv_url + "(.+?)\"", self.html)
            if file_url is None:
                self.error(_("file_url not found"))
            file_url = file_url.group(1)
            long_url = srv_url + file_url
            self.log_debug("long_url = " + long_url)
        else:
            if flashvars['file']:
                file_url = urllib.unquote(flashvars['file'])
            else:
                self.error(_("file_url not found"))

            if url_mode == "3":
                long_url = file_url
                self.log_debug("long_url = " + long_url)
            else:
                long_url = srv_url + "key=" + file_url
                self.log_debug("long_url = " + long_url)

        return long_url


    def get_file_name(self):
        if not self.html:
            self.download_html()

        pattern = r'<title>(.*?) - xHamster\.com</title>'
        name = re.search(pattern, self.html)
        if name is None:
            pattern = r'<h1 >(.*)</h1>'
            name = re.search(pattern, self.html)
            if name is None:
                pattern = r'http://[www.]+xhamster\.com/movies/.*/(.*?)\.html?'
                name = re.match(file_name_pattern, self.pyfile.url)
                if name is None:
                    pattern = r'<div id="element_str_id" style="display:none;">(.*)</div>'
                    name = re.search(pattern, self.html)
                    if name is None:
                        return "Unknown"

        return name.group(1)


    def file_exists(self):
        """
        Returns True or False
        """
        if not self.html:
            self.download_html()
        if re.search(r"(.*Video not found.*)", self.html):
            return False
        else:
            return True
