# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class PremiumizeMe(SimpleHoster):
    __name__    = "PremiumizeMe"
    __type__    = "hoster"
    __version__ = "0.13"

    __pattern__ = r'^unmatchable$'  #: Since we want to allow the user to specify the list of hoster to use we let MultiHoster.coreReady

    __description__ = """Premiumize.me hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Florian Franzen", "FlorianFranzen@gmail.com")]


    MULTI_HOSTER = True


    def handleMulti(self):
        # In some cases hostsers do not supply us with a filename at download, so we
        # are going to set a fall back filename (e.g. for freakshare or xfileshare)
        self.pyfile.name = self.pyfile.name.split('/').pop()  # Remove everthing before last slash

        # Correction for automatic assigned filename: Removing html at end if needed
        suffix_to_remove = ["html", "htm", "php", "php3", "asp", "shtm", "shtml", "cfml", "cfm"]
        temp = self.pyfile.name.split('.')
        if temp.pop() in suffix_to_remove:
            self.pyfile.name = ".".join(temp)

        # Get account data
        user, data = self.account.selectAccount()

        # Get rewritten link using the premiumize.me api v1 (see https://secure.premiumize.me/?show=api)
        data = json_loads(self.load("https://api.premiumize.me/pm-api/v1.php",
                                    get={'method'       : "directdownloadlink",
                                         'params[login]': user,
                                         'params[pass]' : data['password'],
                                         'params[link]' : self.pyfile.url}))

        # Check status and decide what to do
        status = data['status']

        if status == 200:
            self.link = data['result']['location']
            return

        elif status == 400:
            self.fail(_("Invalid link"))

        elif status == 404:
            self.offline()

        elif status >= 500:
            self.tempOffline()

        else:
            self.fail(data['statusmessage'])


getInfo = create_getInfo(PremiumizeMe)
