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
from os.path import exists
from os.path import join

from time import sleep
import sys
from os.path import exists

from os import makedirs

from module.DownloadThread import CaptchaError

class Plugin():
    __name__ = "Plugin"
    __version__ = "0.4"
    __pattern__ = None
    __type__ = "hoster"
    __description__ = """Base Plugin"""
    __author_name__ = ("RaNaN", "spoob", "mkaay")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org", "mkaay@mkaay.de")
    
    def __init__(self, parent):
        self.configparser = parent.core.parser_plugins
        self.config = {}
        self.parent = parent
        self.req = parent.core.requestFactory.getRequest(self.__name__)
        self.html = 0
        self.time_plus_wait = 0 #time() + wait in seconds
        self.want_reconnect = False
        self.multi_dl = True
        self.ocr = None #captcha reader instance
        self.logger = logging.getLogger("log")
        self.decryptNow = True
        self.pyfile = self.parent

    def prepare(self, thread):
        self.want_reconnect = False
        self.pyfile.status.exists = self.file_exists()

        if not self.pyfile.status.exists:
            return False

        self.pyfile.status.filename = self.get_file_name()
        self.pyfile.status.waituntil = self.time_plus_wait
        self.pyfile.status.url = self.get_file_url()
        self.pyfile.status.want_reconnect = self.want_reconnect
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
        header = self.load(self.parent.url, just_header=True)
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
        self.download(url, location)

    def set_config(self):
        for k, v in self.config.items():
            self.configparser.set(self.__name__, {"option": k}, v)

    def remove_config(self, option):
        self.configparser.remove(self.__name__, option)

    def get_config(self, value, default=None):
        self.configparser.loadData()
        return self.configparser.get(self.__name__, value, default=default)

    def read_config(self):
        self.configparser.loadData()
        try:
            self.verify_config()
            self.config = self.configparser.getConfig()[self.__name__]
        except:
            pass
    
    def verify_config(self):
        pass

    def init_ocr(self):
        captchaClass = self.parent.core.pluginManager.getCaptchaPlugin(self.__name__)
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
    
    def waitForCaptcha(self, captchaData, imgType):
        captchaManager = self.parent.core.captchaManager
        task = captchaManager.newTask(self)
        task.setCaptcha(captchaData, imgType)
        task.setWaiting()
        while not task.getStatus() == "done":
            if not self.parent.core.isGUIConnected():
                task.removeTask()
                raise CaptchaError
            sleep(1)
        result = task.getResult()
        task.removeTask()
        return result

    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False):
        return self.req.load(url, get, post, ref, cookies, just_header)
        
    def download(self, url, file_name, get={}, post={}, ref=True, cookies=True):
        download_folder = self.parent.core.config['general']['download_folder']
        if self.pyfile.package.data["package_name"] != (self.parent.core.config['general']['link_file']) and self.parent.core.xmlconfig.get("general", "folder_per_package", False):
            self.pyfile.folder = self.pyfile.package.data["package_name"]
            location = join(download_folder, self.pyfile.folder.decode(sys.getfilesystemencoding()))
            if not exists(location): makedirs(location)
            file_path = join(location.decode(sys.getfilesystemencoding()), self.pyfile.status.filename.decode(sys.getfilesystemencoding()))
        else:
            file_path = join(download_folder, self.pyfile.status.filename.decode(sys.getfilesystemencoding()))
        file_path = join(download_folder, self.pyfile.status.filename.decode(sys.getfilesystemencoding()))
        
        self.pyfile.status.filename = self.req.download(url, file_path, get, post, ref, cookies)
