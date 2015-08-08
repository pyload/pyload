# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class PremiumizeMe(MultiHoster):
    __name__    = "PremiumizeMe"
    __type__    = "hoster"
    __version__ = "0.20"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'  #: Since we want to allow the user to specify the list of hoster to use we let MultiHoster.activate
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Premiumize.me multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Florian Franzen", "FlorianFranzen@gmail.com")]


    def handle_premium(self, pyfile):
        #: In some cases hostsers do not supply us with a filename at download, so we
        #: Are going to set a fall back filename (e.g. for freakshare or xfileshare)
        pyfile.name = pyfile.name.split('/').pop()  #: Remove everthing before last slash

        #: Correction for automatic assigned filename: Removing html at end if needed
        suffix_to_remove = ["html", "htm", "php", "php3", "asp", "shtm", "shtml", "cfml", "cfm"]
        temp = pyfile.name.split('.')
        if temp.pop() in suffix_to_remove:
            pyfile.name = ".".join(temp)

        #: Get account data
        user, info = self.account.select()

        #: Get rewritten link using the premiumize.me api v1 (see https://secure.premiumize.me/?show=api)
        data = json_loads(self.load("http://api.premiumize.me/pm-api/v1.php",  #@TODO: Revert to `https` in 0.4.10
                                    get={'method'       : "directdownloadlink",
                                         'params[login]': user,
                                         'params[pass]' : info['login']['password'],
                                         'params[link]' : pyfile.url}))

        #: Check status and decide what to do
        status = data['status']

        if status == 200:
            self.link = data['result']['location']
            return

        elif status == 400:
            self.fail(_("Invalid link"))

        elif status == 404:
            self.offline()

        elif status >= 500:
            self.temp_offline()

        else:
            self.fail(data['statusmessage'])


getInfo = create_getInfo(PremiumizeMe)
