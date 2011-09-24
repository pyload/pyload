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
    @author: mkaay
"""

from module.plugins.Hoster import Hoster


class Ftp(Hoster):
    __name__ = "Ftp"
    __version__ = "0.31"
    __pattern__ = r'(ftps?|sftp)://(.*?:.*?@)?.*?/.*' # ftp://user:password@ftp.server.org/path/to/file
    __type__ = "hoster"
    __description__ = """A Plugin that allows you to download from an from an ftp directory"""
    __author_name__ = ("jeix", "mkaay")
    __author_mail__ = ("jeix@hasnomail.com", "mkaay@mkaay.de")
    
    def process(self, pyfile):
        pyfile.name = self.pyfile.url.rpartition('/')[2]

        self.chunkLimit = -1
        self.resumeDownload = True

        self.download(pyfile.url)

