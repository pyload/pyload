# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster


class SmoozedCom(MultiHoster):
    __name    = "SmoozedCom"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'^unmatchable$'  #: Since we want to allow the user to specify the list of hoster to use we let MultiHoster.activate
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Smoozed.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("", "")]


    def handlePremium(self, pyfile):
        # In some cases hostsers do not supply us with a filename at download, so we
        # are going to set a fall back filename (e.g. for freakshare or xfileshare)
        pyfile.name = pyfile.name.split('/').pop()  # Remove everthing before last slash

        # Correction for automatic assigned filename: Removing html at end if needed
        suffix_to_remove = ["html", "htm", "php", "php3", "asp", "shtm", "shtml", "cfml", "cfm"]
        temp             = pyfile.name.split('.')

        if temp.pop() in suffix_to_remove:
            pyfile.name = ".".join(temp)

        # Check the link
        get_data = {'session_key': self.account.getAccountInfo(self.user)['session'],
                    'url'        : pyfile.url}

        data = json_loads(self.load("http://www2.smoozed.com/api/check", get=get_data))

        if data["state"] != "ok":
            self.fail(data["message"])

        if data["data"].get("state", "ok") != "ok":
            if data["data"] == "Offline":
                self.offline()
            else:
                self.fail(data["data"]["message"])

        pyfile.name = data["data"]["name"]
        pyfile.size = int(data["data"]["size"])

        # Start the download
        header = self.load("http://www2.smoozed.com/api/download", get=get_data, just_header=True)

        if not "location" in header:
            self.fail(_("Unable to initialize download"))
        else:
            self.link = header["location"][-1] if isinstance(header["location"], list) else header["location"]


    def checkFile(self, rules={}):
        if self.checkDownload({'error': '{"state":"error"}',
                               'retry': '{"state":"retry"}'}):
            self.fail(_("Error response received"))

        return super(SmoozedCom, self).checkFile(rules)
