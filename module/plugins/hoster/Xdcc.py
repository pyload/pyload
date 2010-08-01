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
    __version__ = "0.2"
    __pattern__ = r'xdcc://.*?(/#?.*?)?/.*?/#?\d+/?' # xdcc://irc.Abjects.net/#channel/[XDCC]|Shit/#0004/
    __type__ = "hoster"
    __config__ = [
                    ("nick", "str", "Nickname", "pyload"),
                    ("ident", "str", "Ident", "pyloadident"),
                    ("realname", "str", "Realname", "pyloadreal")
                 ]
    __description__ = """A Plugin that allows you to download from an IRC XDCC bot"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.com")
    
    def process(self, pyfile):
        self.req = pyfile.m.core.requestFactory.getRequest(self.__name__, type="XDCC")        
        self.doDownload(pyfile.url)

    def doDownload(self, url):
        self.pyfile.setStatus("downloading")

        download_folder = self.config['general']['download_folder']
        location = join(download_folder, self.pyfile.package().folder.decode(sys.getfilesystemencoding()))
        if not exists(location): 
            makedirs(location)
            
        m = re.search(r'xdcc://(.*?)/#?(.*?)/(.*?)/#?(\d+)/?', url)
        server = m.group(1)
        chan   = m.group(2)
        bot    = m.group(3)
        pack   = m.group(4)
        nick   = self.getConf('nick')
        ident  = self.getConf('ident')
        real   = self.getConf('realname')
        
        newname = self.req.download(bot, pack, location, nick, ident, real, chan, server)
        self.pyfile.size = self.req.dl_size

        if newname:
            self.pyfile.name = newname
        