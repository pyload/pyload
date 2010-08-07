
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time

from module.plugins.Hoster import Hoster
import hashlib

class RapidshareCom(Hoster):
    __name__ = "RapidshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?rapidshare.com/files/(\d*?)/(.*)"
    __version__ = "1.1"
    __description__ = """Rapidshare.com Download Hoster"""
    __config__ = [ ("server", "str", "Preferred Server", "None") ] 
    __author_name__ = ("spoob", "RaNaN", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "ranan@pyload.org", "mkaay@mkaay.de")

    def setup(self):
        self.html = [None, None]
        self.no_slots = True
        self.api_data = None
        self.multiDL = False
        if self.account:
            self.multiDL = True
            self.req.canContinue = True

    def process(self, pyfile):
        self.url = self.pyfile.url        
        self.prepare()
        self.proceed(self.url)
    
    def getInfo(self):
        self.url = self.pyfile.url
        self.download_api_data()
        self.pyfile.name = self.api_data["filename"]
        self.pyfile.sync()
     
    def prepare(self):
        # self.no_slots = True
        # self.want_reconnect = False

        self.download_api_data()
        if self.api_data["status"] == "1":
            self.pyfile.name = self.get_file_name()

            if self.account:
                info = self.account.getAccountInfo(self.account.getAccountData(self)[0])
                self.log.debug(_("%s: Use Premium Account (%sGB left)") % (self.__name__, info["trafficleft"]/1000/1000))
                if self.api_data["size"] / 1024 > info["trafficleft"]:
                    self.log.info(_("%s: Not enough traffic left" % self.__name__))
                    self.resetAcount()
                else:
                    self.url = self.api_data["mirror"]
                    return True

            self.download_html()
            while self.no_slots:
                self.setWait(self.get_wait_time())
                self.wait()
                # self.pyfile.status.waituntil = self.time_plus_wait
                # self.pyfile.status.want_reconnect = self.want_reconnect
                # thread.wait(self.pyfile)

            self.url = self.get_file_url()

            return True
        elif self.api_data["status"] == "2":
            self.log.info(_("Rapidshare: Traffic Share (direct download)"))
            self.pyfile.name = self.get_file_name()
            # self.pyfile.status.url = self.parent.url
            return True
        else:
            self.fail("Unknown response code.")
            
    def download_api_data(self, force=False):
        """
        http://images.rapidshare.com/apidoc.txt
        """
        if self.api_data and not force:
            return
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_file = {"sub": "checkfiles_v1", "files": "", "filenames": "", "incmd5": "1"}
        m = re.compile(self.__pattern__).search(self.url)
        if m:
            api_param_file["files"] = m.group(1)
            api_param_file["filenames"] = m.group(2)
            src = self.load(api_url_base, cookies=False, get=api_param_file)
            if src.startswith("ERROR"):
                return
            fields = src.split(",")
            self.api_data = {}
            self.api_data["fileid"] = fields[0]
            self.api_data["filename"] = fields[1]
            self.api_data["size"] = int(fields[2]) # in bytes
            self.api_data["serverid"] = fields[3]
            self.api_data["status"] = fields[4]
            """
            status codes:
                0=File not found
                1=File OK (Downloading possible without any logging)
                2=File OK (TrafficShare direct download without any logging)
                3=Server down
                4=File marked as illegal
                5=Anonymous file locked, because it has more than 10 downloads already
                6=File OK (TrafficShare direct download with enabled logging)
            """
            self.api_data["shorthost"] = fields[5]
            self.api_data["checksum"] = fields[6].strip().lower() # md5
            
            self.api_data["mirror"] = "http://rs%(serverid)s%(shorthost)s.rapidshare.com/files/%(fileid)s/%(filename)s" % self.api_data

    def download_html(self):
        """ gets the url from self.parent.url saves html in self.html and parses
        """
        self.html[0] = self.load(self.url, cookies=False)
        
    def get_wait_time(self):
        """downloads html with the important informations
        """
        file_server_url = re.search(r"<form action=\"(.*?)\"", self.html[0]).group(1)
        self.html[1] = self.load(file_server_url, cookies=False, post={"dl.start": "Free"})
        
        if re.search(r"is already downloading", self.html[1]):
            self.log.info(_("Rapidshare: Already downloading, wait 30 minutes"))
            return 30 * 60
        self.no_slots = False
        try:
            wait_minutes = re.search(r"Or try again in about (\d+) minute", self.html[1]).group(1)
            return 60 * int(wait_minutes) + 60
            self.no_slots = True
            self.wantReconnect = True
        except:
            if re.search(r"(Currently a lot of users|no more download slots|servers are overloaded)", self.html[1], re.I) != None:
                self.log.info(_("Rapidshare: No free slots!"))
                self.no_slots = True
                return time() + 130
            self.no_slots = False
            wait_seconds = re.search(r"var c=(.*);.*", self.html[1]).group(1)
            return int(wait_seconds) + 5

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.getConf('server') == "None":
            file_url_pattern = r".*name=\"dlf\" action=\"(.*)\" method=.*"
        else:
            file_url_pattern = '(http://rs.*)\';" /> %s<br />' % getConf('server')

        return re.search(file_url_pattern, self.html[1]).group(1)

    def get_file_name(self):
        if self.api_data["filename"]:
            return self.api_data["filename"]
        elif self.html[0]:
            file_name_pattern = r"<p class=\"downloadlink\">.+/(.+) <font"
            file_name_search = re.search(file_name_pattern, self.html[0])
            if file_name_search:
                return file_name_search.group(1)
        return self.url.split("/")[-1]

    def proceed(self, url):
        self.download(url, get={"directstart":1}, cookies=True)

