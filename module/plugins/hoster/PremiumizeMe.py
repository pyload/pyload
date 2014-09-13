# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.Hoster import Hoster


class PremiumizeMe(Hoster):
    __name__ = "PremiumizeMe"
    __type__ = "hoster"
    __version__ = "0.12"

    __pattern__ = None  #: Since we want to allow the user to specify the list of hoster to use we let MultiHoster.coreReady

    __description__ = """Premiumize.me hoster plugin"""
    __author_name__ = "Florian Franzen"
    __author_mail__ = "FlorianFranzen@gmail.com"


    def process(self, pyfile):
        # Check account
        if not self.account or not self.account.canUse():
            self.logError(_("Please enter your %s account or deactivate this plugin") % "premiumize.me")
            self.fail("No valid premiumize.me account provided")

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

        # Get rewritten link using the premiumize.me api v1 (see https://secure.premiumize.me/?show=api)
        answer = self.load(
            "https://api.premiumize.me/pm-api/v1.php?method=directdownloadlink&params[login]=%s&params[pass]=%s&params[link]=%s" % (
            user, data['password'], pyfile.url))
        data = json_loads(answer)

        # Check status and decide what to do
        status = data['status']
        if status == 200:
            self.download(data['result']['location'], disposition=True)
        elif status == 400:
            self.fail("Invalid link")
        elif status == 404:
            self.offline()
        elif status >= 500:
            self.tempOffline()
        else:
            self.fail(data['statusmessage'])
