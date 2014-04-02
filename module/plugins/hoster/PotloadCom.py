# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the             #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program. If not, see <http://www.gnu.org/licenses/>.     #
############################################################################

# Test links (test.zip):
# http://potload.com/nfzxfl8gntaz



import re


from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp

class PotloadCom(SimpleHoster):
    __name__ = "PotloadCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?potload\.com/[a-z,A-Z,0-9]*"
    __version__ = "0.01"
    __description__ = """Potload.com Download Hoster"""
    __author_name__ = ("duneyr")
    __author_mail__ = ("contact_me_at_github@nomail.com")
    __config__ = []
    
    WAIT_TIME_SEC = 22
    # http://potload.com/nfzxfl8gntaz => nfzxfl8gntaz
    PATTERN_ID_FROM_URL = r'[a-z,A-Z,0-9]{1,}$'
    
    PATTERN_HTML_FILENAME1 = r'<h3>.*\([0-9]*.*</h3>'
    PATTERN_HTML_FILENAME2 = r'>.* \('
    #<h3>test.zip (106 B)</h3> => >test.zip (
    
    PATTERN_HTML_WAITTIME1 = r'You have to wait [0-9]* seconds till next download'
    PATTERN_HTML_WAITTIME2 = r'[0-9]{1,}'
    
    PATTERN_HTML_TOKEN = r'rand" value="[a-z,0-9]*'
    
    PATTERN_HTML_TARGET_URL = r'downloadurl">[^/d]*<a href="[^"]*'
    
    def setup(self):
        self.multiDL = False
        
    def process(self, pyfile):
       
        # initial page
        firstpage=self.load(pyfile.url, cookies=True)
        
        # check for offline
        if not re.search("<h2>DOWNLOAD FILE:</h2>", firstpage, flags=re.IGNORECASE):
            self.offline()
            return	        
        
        
        # get filename (for post data)
        ret = re.search(self.PATTERN_HTML_FILENAME1, firstpage, flags=re.IGNORECASE)
        form = ret.group(0)
        ret = re.search(self.PATTERN_HTML_FILENAME2, form, flags=re.IGNORECASE)
        extract = ret.group(0)
        filename = extract[1:-2]
        self.pyfile.name = filename
        

        # check wait time
        ret = re.search(self.PATTERN_HTML_WAITTIME1, firstpage, flags=re.IGNORECASE)
        if ret:
            form = ret.group(0)
            ret = re.search(self.PATTERN_HTML_WAITTIME2, form, flags=re.IGNORECASE)
            extract = int(ret.group(0))+1
            self.setWait(extract)
            self.logDebug("PotLoad: too many downloads -> wait %d seconds" % extract)
            self.wait()      
        
        # page where we have to wait (and submit first pkg of data)
        secondpage = self.load(pyfile.url, post={"op": "download1", "usr_login": "", "id": re.search(self.PATTERN_ID_FROM_URL, pyfile.url).group(0),
            "fname":filename, "referer":pyfile.url, "method_free":"Slow+Download"},
            cookies=True)
        
        
        # get token
        ret = re.search(self.PATTERN_HTML_TOKEN, secondpage, flags=re.IGNORECASE | re.DOTALL)
        token = ret.group(0)[13:]

		
        self.setWait(self.WAIT_TIME_SEC)
        self.logDebug("PotLoad: regular wait %d seconds" % self.WAIT_TIME_SEC)
        self.wait()      
        
        # get page which provides link
        thirdpage = self.load(pyfile.url, post={"op": "download2", "usr_login": "", "id": re.search(self.PATTERN_ID_FROM_URL, pyfile.url).group(0),
            "fname":filename, "referer":pyfile.url, "method_free":"Slow+Download", "rand":token},
            cookies=True)
        
        # filter link
        ret = re.search(self.PATTERN_HTML_TARGET_URL, thirdpage, flags=re.IGNORECASE | re.DOTALL)
        link = ret.group(0)[25:]

        
        
        self.download(link, disposition=True)
		
		

