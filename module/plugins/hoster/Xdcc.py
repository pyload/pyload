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
import re
import sys

from module.plugins.Hoster import Hoster


class Xdcc(Hoster):
    __name__ = "Xdcc"
    __version__ = "0.1"
    __pattern__ = r'xdcc://.*?/.*?/#?\d+/?' # xdcc://irc.Abjects.net/[XDCC]|Shit/#0004/
    __type__ = "hoster"
    __description__ = """A Plugin that allows you to download from an IRC XDCC bot"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.com")
    
    def __init__(self, parent):
        self.parent = parent
        self.req = parent.core.requestFactory.getRequest(self.__name__, type="XDCC")
        self.want_reconnect = False
        self.multi_dl = True
        self.logger = logging.getLogger("log")
        self.pyfile = self.parent

    def prepare(self, thread):
        self.pyfile.status.url = self.parent.url
        thread.wait(self.parent)
        return True

    def proceed(self, url, location):
        download_folder = self.parent.core.config['general']['download_folder']
        location = download_folder
        if self.pyfile.package.data["package_name"] != (self.parent.core.config['general']['link_file']) and self.parent.core.xmlconfig.get("general", "folder_per_package", False):
            self.pyfile.folder = self.pyfile.package.data["package_name"]
            location = join(download_folder, self.pyfile.folder.decode(sys.getfilesystemencoding()))
            if not exists(location):
                makedirs(location)

        m = re.search(r'xdcc://(.*?)/(.*?)/#?(\d+)/?', url)
        server = m.group(1)
        bot    = m.group(2)
        pack   = m.group(3)
        nick   = self.parent.core.config['xdcc']['nick']
        ident  = self.parent.core.config['xdcc']['ident']
        real   = self.parent.core.config['xdcc']['realname']
        
        self.pyfile.status.filename = self.req.download(bot, pack, location, nick, ident, real, server)
