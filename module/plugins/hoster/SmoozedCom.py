# -*- coding: utf-8 -*-

from module.plugins.Hoster import Hoster

from module.common.json_layer import json_loads


class SmoozedCom(Hoster):
    __name__    = "SmoozedCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'^unmatchable$'  #: Since we want to allow the user to specify the list of hoster to use we let MultiHoster.coreReady

    __description__ = """Smoozed.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = []


    def process(self, pyfile):
        # Check account
        if not self.account or not self.account.canUse():
            self.logError(_("Please enter your %s account or deactivate this plugin") % "smoozed.com")
            self.fail(_("No valid smoozed.com account provided"))

        # In some cases hostsers do not supply us with a filename at download, so we
        # are going to set a fall back filename (e.g. for freakshare or xfileshare)
        pyfile.name = pyfile.name.split('/').pop()  # Remove everthing before last slash

        # Correction for automatic assigned filename: Removing html at end if needed
        suffix_to_remove = ["html", "htm", "php", "php3", "asp", "shtm", "shtml", "cfml", "cfm"]
        temp = pyfile.name.split('.')
        if temp.pop() in suffix_to_remove:
            pyfile.name = ".".join(temp)

        # Get account data
        (user, data) = self.account.selectAccount()
        account_info = self.account.getAccountInfo(user, True)

        # Check the link
        get_data = {
            "session_key": account_info['session_key'],
            "url": pyfile.url
        }
        answer = self.load("http://www2.smoozed.com/api/check", get=get_data)
        data = json_loads(answer)
        if data["state"] != "ok":
            self.fail(_(data["message"]))
        if data["data"].get("state", "ok") != "ok":
            if data["data"] == "Offline":
                self.offline()
            else:
                self.fail(_(data["data"]["message"]))
        pyfile.name = data["data"]["name"]
        pyfile.size = int(data["data"]["size"])

        # Start the download
        header = self.load("http://www2.smoozed.com/api/download", get=get_data, just_header=True)
        if not "location" in header:
            self.fail(_("Unable to initialize download"))

        if isinstance(header["location"], list):
            url = header["location"][-1]
        else:
            url = header["location"]
        self.download(url, disposition=True)

        check = self.checkDownload({"error": '{"state":"error"}', "retry": '{"state":"retry"}'})
        if check == "error" or check == "retry":
            self.fail(_("Error response received - contact Smoozed support"))
