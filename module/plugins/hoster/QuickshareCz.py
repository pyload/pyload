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

    @author: zoidberg
"""

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from pycurl import FOLLOWLOCATION

class QuickshareCz(SimpleHoster):
    __name__ = "QuickshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://.*quickshare.cz/stahnout-soubor/.*"
    __version__ = "0.54"
    __description__ = """Quickshare.cz"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<th width="145px">Název:</th>\s*<td style="word-wrap:break-word;">(?P<N>[^<]+)</td>'
    FILE_SIZE_PATTERN = r'<th>Velikost:</th>\s*<td>(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</td>'
    FILE_OFFLINE_PATTERN = r'<script type="text/javascript">location.href=\'/chyba\';</script>'

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode = True)
        self.getFileInfo()
        
        # parse js variables
        self.jsvars = dict((x, y.strip("'")) for x,y in re.findall(r"var (\w+) = ([0-9.]+|'[^']*')", self.html))
        self.logDebug(self.jsvars)        
        pyfile.name = self.jsvars['ID3']
        
        # determine download type - free or premium
        if self.premium:
            if 'UU_prihlasen' in self.jsvars:
                if self.jsvars['UU_prihlasen'] == '0':
                    self.logWarning('User not logged in')
                    self.relogin(self.user)
                    self.retry()
                elif float(self.jsvars['UU_kredit']) < float(self.jsvars['kredit_odecet']):
                    self.logWarning('Not enough credit left')
                    self.premium = False
                
        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()
            
        check = self.checkDownload({"err": re.compile(r"\AChyba!")}, max_size=100)
        if check == "err":
            self.fail("File not found or plugin defect")
                   
    def handleFree(self):               
        # get download url
        download_url = '%s/download.php' % self.jsvars['server']
        data = dict((x, self.jsvars[x]) for x in self.jsvars if x in ('ID1', 'ID2', 'ID3', 'ID4'))
        self.logDebug("FREE URL1:" + download_url, data)
               
        self.req.http.c.setopt(FOLLOWLOCATION, 0)        
        self.load(download_url, post=data)
        self.header = self.req.http.header        
        self.req.http.c.setopt(FOLLOWLOCATION, 1)
        
        found = re.search("Location\s*:\s*(.*)", self.header, re.I)
        if not found: self.fail('File not found')
        download_url = found.group(1)                        
        self.logDebug("FREE URL2:" + download_url)
        
        # check errors
        found = re.search(r'/chyba/(\d+)', download_url)
        if found:
            if found.group(1) == '1':
                self.retry(max_tries=60, wait_time=120, reason="This IP is already downloading")
            elif found.group(1) == '2':
                self.retry(max_tries=60, wait_time=60, reason="No free slots available")
            else:
                self.fail('Error %d' % found.group(1))

        # download file
        self.download(download_url)   
    
    def handlePremium(self):
        download_url = '%s/download_premium.php' % self.jsvars['server']
        data = dict((x, self.jsvars[x]) for x in self.jsvars if x in ('ID1', 'ID2', 'ID4', 'ID5'))
        self.logDebug("PREMIUM URL:" + download_url, data)
        self.download(download_url, get=data)

getInfo = create_getInfo(QuickshareCz)
