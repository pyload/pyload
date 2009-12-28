# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN, spoob, mkaay
"""

import logging
import re
from os.path import exists, join


from module.network.Request import Request
from module.XMLConfigParser import XMLConfigParser

class Plugin():

    def __init__(self, parent):
        self.configparser = XMLConfigParser(join("module","config","plugin.xml"), join("module","config","plugin_default.xml"))
        self.config = {}
        props = {}
        props['name'] = "BasePlugin"
        props['version'] = "0.2"
        props['pattern'] = None
        props['type'] = "hoster"
        props['description'] = """Base Plugin"""
        props['author_name'] = ("RaNaN", "spoob", "mkaay")
        props['author_mail'] = ("RaNaN@pyload.org", "spoob@pyload.org", "mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.req = Request()
        self.html = 0
        self.time_plus_wait = 0 #time() + wait in seconds
        self.want_reconnect = False
        self.multi_dl = True
        self.ocr = None #captcha reader instance
        self.logger = logging.getLogger("log")
    
    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False

        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            raise Exception, "File not found"
            return False

        pyfile.status.filename = self.get_file_name()
            
        pyfile.status.waituntil = self.time_plus_wait
        pyfile.status.url = self.get_file_url()
        pyfile.status.want_reconnect = self.want_reconnect

        thread.wait(self.parent)

        return True

    def set_parent_status(self):
        """ sets all available Statusinfos about a File in self.parent.status
        """
        pass

    def download_html(self):
        """ gets the url from self.parent.url saves html in self.html and parses
        """
        self.html = ""

    def file_exists(self):
        """ returns True or False
        """
        if re.search(r"(?!http://).*\.(dlc|ccf|rsdf|txt)", self.parent.url):
            return exists(self.parent.url)
        header = self.req.load(self.parent.url, just_header=True)
        try:
            if re.search(r"HTTP/1.1 404 Not Found", header):
                return False
        except:
            pass
        return True

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        return self.parent.url

    def get_file_name(self):
        try:
            return re.findall("([^\/=]+)", self.parent.url)[-1]
        except:
            return self.parent.url[:20]

    def wait_until(self):
        if self.html != None:
            self.download_html()
        return self.time_plus_wait

    def proceed(self, url, location):
        self.req.download(url, location)

    def set_config(self):
        for k, v in self.config:
            self.configparser.set(self.props['name'], k, v)

    def get_config(self, value):
        self.configparser.loadData()
        return self.configparser.get(self.props['name'], value)

    def read_config(self):
        self.configparser.loadData()
        try:
            self.config = self.configparser.getConfig()[self.props['name']]
        except:
            pass

    def init_ocr(self):
        modul = __import__("module.captcha." + self.props['name'], fromlist=['captcha'])
        captchaClass = getattr(modul, self.props['name'])
        self.ocr = captchaClass()

    def __call__(self):
        return self.props['name']
    
    def check_file(self, local_file):
        """
        return codes:
        0  - checksum ok
        1  - checksum wrong
        5  - can't get checksum
        10 - not implemented
        20 - unknown error
        """
    	return (True, 10)
