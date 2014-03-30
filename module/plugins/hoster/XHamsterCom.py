# -*- coding: utf-8 -*-

import re
from urllib import unquote

from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads


def clean_json(json_expr):
    json_expr = re.sub('[\n\r]', '', json_expr)
    json_expr = re.sub(' +', '', json_expr)
    json_expr = re.sub('\'', '"', json_expr)

    return json_expr


class XHamsterCom(Hoster):
    __name__ = "XHamsterCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?xhamster\.com/movies/.+"
    __version__ = "0.12"
    __config__ = [("type", ".mp4;.flv", "Preferred type", ".mp4")]
    __description__ = """XHamster.com hoster plugin"""

    def process(self, pyfile):
        self.pyfile = pyfile

        if not self.file_exists():
            self.offline()

        if self.getConfig("type"):
            self.desired_fmt = self.getConfig("type")

        self.pyfile.name = self.get_file_name() + self.desired_fmt
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()

        flashvar_pattern = re.compile('flashvars = ({.*?});', re.DOTALL)
        json_flashvar = flashvar_pattern.search(self.html)

        if json_flashvar is None:
            self.fail("Parse error (flashvars)")

        j = clean_json(json_flashvar.group(1))
        flashvars = json_loads(j)

        if flashvars["srv"]:
            srv_url = flashvars["srv"] + '/'
        else:
            self.fail("Parse error (srv_url)")

        if flashvars["url_mode"]:
            url_mode = flashvars["url_mode"]
        else:
            self.fail("Parse error (url_mode)")

        if self.desired_fmt == ".mp4":
            file_url = re.search(r"<a href=\"" + srv_url + "(.+?)\"", self.html)
            if file_url is None:
                self.fail("Parse error (file_url)")
            file_url = file_url.group(1)
            long_url = srv_url + file_url
            self.logDebug("long_url: %s" % long_url)
        else:
            if flashvars["file"]:
                file_url = unquote(flashvars["file"])
            else:
                self.fail("Parse error (file_url)")

            if url_mode == '3':
                long_url = file_url
                self.logDebug("long_url: %s" % long_url)
            else:
                long_url = srv_url + "key=" + file_url
                self.logDebug("long_url: %s" % long_url)

        return long_url

    def get_file_name(self):
        if self.html is None:
            self.download_html()

        file_name_pattern = r"<title>(.*?) - xHamster\.com</title>"
        file_name = re.search(file_name_pattern, self.html)
        if file_name is None:
            file_name_pattern = r"<h1 >(.*)</h1>"
            file_name = re.search(file_name_pattern, self.html)
            if file_name is None:
                file_name_pattern = r"http://[www.]+xhamster\.com/movies/.*/(.*?)\.html?"
                file_name = re.match(file_name_pattern, self.pyfile.url)
                if file_name is None:
                    file_name_pattern = r"<div id=\"element_str_id\" style=\"display:none;\">(.*)</div>"
                    file_name = re.search(file_name_pattern, self.html)
                    if file_name is None:
                        return "Unknown"

        return file_name.group(1)

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
        if re.search(r"(.*Video not found.*)", self.html) is not None:
            return False
        else:
            return True
