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
    __version__ = "0.2"
    __pattern__ = r'ftp://(.*?:.*?@)?.*?/.*' # ftp://user:password@ftp.server.org/path/to/file
    __type__ = "hoster"
    __description__ = """A Plugin that allows you to download from an from an ftp directory"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.com")
    
    def process(self, pyfile):
        self.req = pyfile.m.core.requestFactory.getRequest(self.__name__, type="FTP")
        pyfile.name = get_file_name()
        
        self.doDownload(pyfile.url, pyfile.name)

        
    def get_file_name(self):
        return self.parent.url.rpartition('/')[2]
        
        
    def doDownload(self, url, filename):
        self.pyfile.setStatus("downloading")
        
        download_folder = self.config['general']['download_folder']
        location = join(download_folder, self.pyfile.package().folder.decode(sys.getfilesystemencoding()))
        if not exists(location): 
            makedirs(location)

        newname = self.req.download(url, join(location,filename.decode(sys.getfilesystemencoding())))
        self.pyfile.size = self.req.dl_size

        if newname:
            self.pyfile.name = newname
