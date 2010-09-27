
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.network.Request import getURL
from module.plugins.Hoster import Hoster

def getInfo(urls):
    
    ids = ""
    names = ""
    
    for url in urls:
        tmp = url.split("/")
        ids+= ","+tmp[-2]
        names+= ","+tmp[-1]
    
    url = "http://api.rapidshare.com/cgi-bin/rsapi.cgi?sub=checkfiles_v1&files=%s&filenames=%s" % (ids[1:], names[1:])
    
    
    api = getURL(url)
    result = []
    i = 0
    for res in api.split():
        tmp = res.split(",")
        if tmp[4] in ("0", "4", "5"): status = 1
        elif tmp[4] == "1": status = 2
        else: status = 3
        
        result.append( (tmp[1], tmp[2], status, urls[i]) ) 
        i += 1
        
    yield result

class RapidshareCom(Hoster):
    __name__ = "RapidshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?rapidshare.com/files/(\d*?)/(.*)"
    __version__ = "2.0"
    __description__ = """Rapidshare.com Download Hoster"""
    __config__ = [["server", "Cogent;Deutsche Telekom;Level(3);Level(3) #2;GlobalCrossing;Level(3) #3;Teleglobe;GlobalCrossing #2;TeliaSonera #2;Teleglobe #2;TeliaSonera #3;TeliaSonera", "Preferred Server", "None"]] 
    __author_name__ = ("spoob", "RaNaN", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "ranan@pyload.org", "mkaay@mkaay.de")

    def setup(self):
        self.html = [None, None]
        self.no_download = True
        self.api_data = None
        self.multiDL = False
        self.direct = False
        if self.account:
            self.multiDL = True
            self.req.canContinue = True

    def process(self, pyfile):
        self.url = self.pyfile.url        
        self.prepare()
         
    def prepare(self):
        # self.no_slots = True
        # self.want_reconnect = False

        self.download_api_data()
        if self.api_data["status"] == "1":
            self.pyfile.name = self.get_file_name()

            if self.account:
                self.handlePremium()
            else:
                self.handleFree()

        elif self.api_data["status"] == "2":
            self.log.info(_("Rapidshare: Traffic Share (direct download)"))
            self.pyfile.name = self.get_file_name()
            # self.pyfile.status.url = self.parent.url

            self.download(self.pyfile.url, get={"directstart":1}, cookies=True)

        elif int(self.api_data["status"]) >= 50 and int(self.api_data["status"]) < 100:
            self.pyfile.name = self.get_file_name()
            self.direct = True

            self.download(self.pyfile.url)

        else:
            self.fail("Unknown response code.")

    def handleFree(self):

        while self.no_download:
            dl_dict = self.freeWait()


        download = "http://%(host)s/cgi-bin/rsapi.cgi?sub=download_v1&editparentlocation=1&bin=1&fileid=%(id)s&filename=%(name)s&dlauth=%(auth)s#!download|%(server)s|%(id)s|%(name)s|%(size)s" % dl_dict

        self.download(download)

    def handlePremium(self):
        info = self.account.getAccountInfo(self.account.getAccountData(self)[0])
        self.log.debug(_("%(name)s: Use Premium Account (%(left)sGB left)") % { "name" : self.__name__, "left": info["trafficleft"]/1000/1000 })
        if self.api_data["size"] / 1024 > info["trafficleft"]:
            self.log.info(_("%s: Not enough traffic left" % self.__name__))
            #self.resetAcount() #@TODO implement
        else:
            url = self.api_data["mirror"]
            self.download(url, get={"directstart":1}, cookies=True)


    def download_api_data(self, force=False):
        """
        http://images.rapidshare.com/apidoc.txt
        """
        if self.api_data and not force:
            return
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_file = {"sub": "checkfiles_v1", "files": "", "filenames": "", "incmd5": "1"}
        m = re.search(self.__pattern__, self.url)
        if m:
            api_param_file["files"] = m.group(1)
            api_param_file["filenames"] = m.group(2)
            src = self.load(api_url_base, cookies=False, get=api_param_file).strip()
            self.log.debug("RS INFO API: %s" % src)
            if src.startswith("ERROR"):
                return
            fields = src.split(",")
            self.api_data = {"fileid": fields[0], "filename": fields[1], "size": int(fields[2]), "serverid": fields[3],
                             "status": fields[4]}
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

    def freeWait(self):
        """downloads html with the important informations
        """
        self.html[1] = self.load(self.pyfile.url)
        self.no_download = True

        m = re.search(self.__pattern__, self.url)

        id = m.group(1)
        name = m.group(2)

        prepare = "http://api.rapidshare.com/cgi-bin/rsapi.cgi?sub=download_v1&fileid=%(id)s&filename=%(name)s&try=1&cbf=RSAPIDispatcher&cbid=1" % {"name": name, "id" : id}

        result = self.load(prepare)

        self.log.debug("RS API Result: %s" % result)

        between_wait = re.search("You need to wait (\d+) seconds", result)

        if between_wait:
            self.setWait(int(between_wait.group(1)))
            self.wantReconnect = True
            self.wait()
        else:
            self.no_download = False

            tmp, info = result.split(":")
            data = info.split(",")

            dl_dict = {"id": id,
                        "name": name,
                        "host": data[0],
                        "auth": data[1],
                        "server": self.api_data["serverid"],
                        "size": self.api_data["size"]
            }
            self.setWait(int(data[2]))
            self.wait()

            return dl_dict


    def get_file_name(self):
        if self.api_data["filename"]:
            return self.api_data["filename"]
        return self.url.split("/")[-1]

