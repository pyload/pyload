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
from urlparse import urlparse, urljoin
from urllib import quote, unquote
import pycurl, re

from module.plugins.Hoster import Hoster
from module.network.HTTPRequest import BadHeader

class Ftp(Hoster):
    __name__ = "Ftp"
    __version__ = "0.41"
    __pattern__ = r'(ftps?|sftp)://(.*?:.*?@)?.*?/.*' # ftp://user:password@ftp.server.org/path/to/file
    __type__ = "hoster"
    __description__ = """A Plugin that allows you to download from an from an ftp directory"""
    __author_name__ = ("jeix", "mkaay", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.com", "mkaay@mkaay.de", "zoidberg@mujmail.cz")
    
    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True   
    
    def process(self, pyfile):
        parsed_url = urlparse(pyfile.url)
        netloc = parsed_url.netloc
        
        pyfile.name = parsed_url.path.rpartition('/')[2]
        try:
            pyfile.name = unquote(str(pyfile.name)).decode('utf8')
        except:
            pass        
        
        if not "@" in netloc:
            servers = [ x['login'] for x in self.account.getAllAccounts() ] if self.account else []                             
                
            if netloc in servers:
                self.logDebug("Logging on to %s" % netloc)                
                self.req.addAuth(self.account.accounts[netloc]["password"])
            else:
                for pwd in pyfile.package().password.splitlines(): 
                    if ":" in pwd:
                        self.req.addAuth(pwd.strip())
                        break                            
        
        self.req.http.c.setopt(pycurl.NOBODY, 1)
        
        try:
            response = self.load(pyfile.url)
        except pycurl.error, e:
            self.fail("Error %d: %s" % e.args)
        
        self.req.http.c.setopt(pycurl.NOBODY, 0)        
        self.logDebug(self.req.http.header)
        
        found = re.search(r"Content-Length:\s*(\d+)", response)
        if found:
            pyfile.size = int(found.group(1))                 
            self.download(pyfile.url)
        else:
            #Naive ftp directory listing          
            if re.search(r'^25\d.*?"', self.req.http.header, re.M):            
                pyfile.url = pyfile.url.rstrip('/')
                pkgname = "/".join((pyfile.package().name,urlparse(pyfile.url).path.rpartition('/')[2]))
                pyfile.url += '/'
                self.req.http.c.setopt(48, 1) # CURLOPT_DIRLISTONLY
                response = self.load(pyfile.url, decode = False)
                links = [ pyfile.url + quote(x) for x in response.splitlines() ]
                self.logDebug("LINKS", links)
                self.core.api.addPackage(pkgname, links, 1)
                #self.core.files.addLinks(links, pyfile.package().id)
            else:
                self.fail("Unexpected server response")
            
        