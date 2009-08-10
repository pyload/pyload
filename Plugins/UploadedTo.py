#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time
from Plugin import Plugin

class UploadedTo(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "UploadedTo"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www\.)?u(?:p)?l(?:oaded)?\.to/"
        props['version'] = "0.1"
        props['description'] = """Uploaded.to Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.want_reconnect = None
        self.multi_dl = False

    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False
        tries = 0

        while not pyfile.status.url:

            self.download_html()

            pyfile.status.exists = self.file_exists()

            if not pyfile.status.exists:
                raise Exception, "The file was not found on the server."

            pyfile.status.filename = self.get_file_name()

            pyfile.status.waituntil = self.time_plus_wait
            pyfile.status.url = self.get_file_url()
            pyfile.status.want_reconnect = self.want_reconnect

            thread.wait(self.parent)

            tries += 1
            if tries > 5:
                raise Exception, "Error while preparing DL, HTML dump: %s" % self.html

        return True

    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url)

        try:
            wait_minutes = re.search(r"Or wait (\d+) minutes", self.html).group(1)
            self.time_plus_wait = time() + 60 * int(wait_minutes)
            self.want_reconnect = True
        except:
            self.time_plus_wait = 0

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        try:
            file_url_pattern = r".*<form name=\"download_form\" method=\"post\" action=\"(.*)\">"
            return re.search(file_url_pattern, self.html).group(1)
        except:
            return None

    def get_file_name(self):
        if not self.want_reconnect:
            file_name = re.search(r"<td><b>\s+(.+)\s", self.html).group(1)
            file_suffix = re.search(r"</td><td>(\..+)</td></tr>", self.html)
            if not file_suffix:
                return file_name
            return file_name + file_suffix.group(1)
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if re.search(r"(File doesn't exist .*)", self.html) != None:
            return False
        else:
            return True
