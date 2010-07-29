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
    
    @author: jeix
"""

import logging
from os.path import exists
from os.path import join
from os.path import exists
from os import makedirs
import sys

from module.plugins.Hoster import Hoster


class Ftp(Hoster):
    __name__ = "Ftp"
    __version__ = "0.1"
    __pattern__ = r'ftp://(.*?:.*?@)?.*?/.*' # ftp://user:password@ftp.server.org/path/to/file
    __type__ = "hoster"
    __description__ = """A Plugin that allows you to download from an from an ftp directory"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.com")
    
    def __init__(self, parent):
        self.parent = parent
        self.req = parent.core.requestFactory.getRequest(self.__name__, type="FTP")
        self.want_reconnect = False
        self.multi_dl = True
        self.logger = logging.getLogger("log")
        self.pyfile = self.parent

    def prepare(self, thread):
        self.pyfile.status.url = self.parent.url
        self.pyfile.status.filename = self.get_file_name()
        thread.wait(self.parent)
        return True
        
    def get_file_name(self):
        return self.parent.url.rpartition('/')[2]

    def proceed(self, url, location):
        download_folder = self.parent.core.config['general']['download_folder']
        if self.pyfile.package.data["package_name"] != (self.parent.core.config['general']['link_file']) and self.parent.core.xmlconfig.get("general", "folder_per_package", False):
            self.pyfile.folder = self.pyfile.package.data["package_name"]
            location = join(download_folder, self.pyfile.folder.decode(sys.getfilesystemencoding()))
            if not exists(location): makedirs(location)
            file_path = join(location.decode(sys.getfilesystemencoding()), self.pyfile.status.filename.decode(sys.getfilesystemencoding()))
        else:
            file_path = join(download_folder, self.pyfile.status.filename.decode(sys.getfilesystemencoding()))

        self.pyfile.status.filename = self.req.download(url, file_path)
