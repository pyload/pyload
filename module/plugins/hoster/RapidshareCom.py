# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster


def getInfo(urls):
    ids = ""
    names = ""

    p = re.compile(RapidshareCom.__pattern__)

    for url in urls:
        r = p.search(url)
        if r.group("name"):
            ids += "," + r.group("id")
            names += "," + r.group("name")
        elif r.group("name_new"):
            ids += "," + r.group("id_new")
            names += "," + r.group("name_new")

    url = "http://api.rapidshare.com/cgi-bin/rsapi.cgi?sub=checkfiles&files=%s&filenames=%s" % (ids[1:], names[1:])

    api = getURL(url)
    result = []
    i = 0
    for res in api.split():
        tmp = res.split(",")
        if tmp[4] in ("0", "4", "5"):
            status = 1
        elif tmp[4] == "1":
            status = 2
        else:
            status = 3

        result.append((tmp[1], tmp[2], status, urls[i]))
        i += 1

    yield result


class RapidshareCom(Hoster):
    __name__ = "RapidshareCom"
    __type__ = "hoster"
    __version__ = "1.39"

    __pattern__ = r'https?://(?:www\.)?rapidshare.com/(?:files/(?P<id>\d*?)/(?P<name>[^?]+)|#!download\|(?:\w+)\|(?P<id_new>\d+)\|(?P<name_new>[^|]+))'
    __config__ = [("server",
                   "Cogent;Deutsche Telekom;Level(3);Level(3) #2;GlobalCrossing;Level(3) #3;Teleglobe;GlobalCrossing #2;TeliaSonera #2;Teleglobe #2;TeliaSonera #3;TeliaSonera",
                   "Preferred Server", "None")]

    __description__ = """Rapidshare.com hoster plugin"""
    __author_name__ = ("spoob", "RaNaN", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "ranan@pyload.org", "mkaay@mkaay.de")


    def setup(self):
        self.no_download = True
        self.api_data = None
        self.offset = 0
        self.dl_dict = {}

        self.id = None
        self.name = None

        self.chunkLimit = -1 if self.premium else 1
        self.multiDL = self.resumeDownload = self.premium

    def process(self, pyfile):
        self.url = pyfile.url
        self.prepare()

    def prepare(self):
        m = re.match(self.__pattern__, self.url)

        if m.group("name"):
            self.id = m.group("id")
            self.name = m.group("name")
        else:
            self.id = m.group("id_new")
            self.name = m.group("name_new")

        self.download_api_data()
        if self.api_data['status'] == "1":
            self.pyfile.name = self.get_file_name()

            if self.premium:
                self.handlePremium()
            else:
                self.handleFree()

        elif self.api_data['status'] == "2":
            self.logInfo(_("Rapidshare: Traffic Share (direct download)"))
            self.pyfile.name = self.get_file_name()

            self.download(self.pyfile.url, get={"directstart": 1})

        elif self.api_data['status'] in ("0", "4", "5"):
            self.offline()
        elif self.api_data['status'] == "3":
            self.tempOffline()
        else:
            self.fail("Unknown response code.")

    def handleFree(self):
        while self.no_download:
            self.dl_dict = self.freeWait()

        #tmp = "#!download|%(server)s|%(id)s|%(name)s|%(size)s"
        download = "http://%(host)s/cgi-bin/rsapi.cgi?sub=download&editparentlocation=0&bin=1&fileid=%(id)s&filename=%(name)s&dlauth=%(auth)s" % self.dl_dict

        self.logDebug("RS API Request: %s" % download)
        self.download(download, ref=False)

        check = self.checkDownload({"ip": "You need RapidPro to download more files from your IP address",
                                    "auth": "Download auth invalid"})
        if check == "ip":
            self.setWait(60)
            self.logInfo(_("Already downloading from this ip address, waiting 60 seconds"))
            self.wait()
            self.handleFree()
        elif check == "auth":
            self.logInfo(_("Invalid Auth Code, download will be restarted"))
            self.offset += 5
            self.handleFree()

    def handlePremium(self):
        info = self.account.getAccountInfo(self.user, True)
        self.logDebug("%s: Use Premium Account" % self.__name__)
        url = self.api_data['mirror']
        self.download(url, get={"directstart": 1})

    def download_api_data(self, force=False):
        """
        http://images.rapidshare.com/apidoc.txt
        """
        if self.api_data and not force:
            return
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_file = {"sub": "checkfiles", "incmd5": "1", "files": self.id, "filenames": self.name}
        src = self.load(api_url_base, cookies=False, get=api_param_file).strip()
        self.logDebug("RS INFO API: %s" % src)
        if src.startswith("ERROR"):
            return
        fields = src.split(",")

        # status codes:
        #   0=File not found
        #   1=File OK (Anonymous downloading)
        #   3=Server down
        #   4=File marked as illegal
        #   5=Anonymous file locked, because it has more than 10 downloads already
        #   50+n=File OK (TrafficShare direct download type "n" without any logging.)
        #   100+n=File OK (TrafficShare direct download type "n" with logging.
        #                  Read our privacy policy to see what is logged.)

        self.api_data = {"fileid": fields[0], "filename": fields[1], "size": int(fields[2]), "serverid": fields[3],
                         "status": fields[4], "shorthost": fields[5], "checksum": fields[6].strip().lower()}

        if int(self.api_data['status']) > 100:
            self.api_data['status'] = str(int(self.api_data['status']) - 100)
        elif int(self.api_data['status']) > 50:
            self.api_data['status'] = str(int(self.api_data['status']) - 50)

        self.api_data['mirror'] = "http://rs%(serverid)s%(shorthost)s.rapidshare.com/files/%(fileid)s/%(filename)s" % self.api_data

    def freeWait(self):
        """downloads html with the important information
        """
        self.no_download = True

        id = self.id
        name = self.name

        prepare = "https://api.rapidshare.com/cgi-bin/rsapi.cgi?sub=download&fileid=%(id)s&filename=%(name)s&try=1&cbf=RSAPIDispatcher&cbid=1" % {
            "name": name, "id": id}

        self.logDebug("RS API Request: %s" % prepare)
        result = self.load(prepare, ref=False)
        self.logDebug("RS API Result: %s" % result)

        between_wait = re.search("You need to wait (\d+) seconds", result)

        if "You need RapidPro to download more files from your IP address" in result:
            self.setWait(60)
            self.logInfo(_("Already downloading from this ip address, waiting 60 seconds"))
            self.wait()
        elif ("Too many users downloading from this server right now" in result or
              "All free download slots are full" in result):
            self.setWait(120)
            self.logInfo(_("RapidShareCom: No free slots"))
            self.wait()
        elif "This file is too big to download it for free" in result:
            self.fail(_("You need a premium account for this file"))
        elif "Filename invalid." in result:
            self.fail(_("Filename reported invalid"))
        elif between_wait:
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
                       "server": self.api_data['serverid'],
                       "size": self.api_data['size']}
            self.setWait(int(data[2]) + 2 + self.offset)
            self.wait()

            return dl_dict

    def get_file_name(self):
        if self.api_data['filename']:
            return self.api_data['filename']
        return self.url.split("/")[-1]
