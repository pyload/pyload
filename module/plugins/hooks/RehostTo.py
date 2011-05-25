# -*- coding: utf-8 -*-
import re

from module.network.RequestFactory import getURL
from module.plugins.Hook import Hook

from module.utils import removeChars

class RehostTo(Hook):
    __name__ = "RehostTo"
    __version__ = "0.4"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False")]

    __description__ = """rehost.to hook plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    interval = 0
    hosters = []

    replacements = [("freakshare.net", "freakshare.com")]

    def getHostersCached(self):
        if not self.hosters:

            page = getURL("http://rehost.to/api.php?cmd=get_supported_och_dl&long_ses=%s" % self.long_ses)

            self.hosters = [x.strip() for x in page.replace("\"", "").split(",")]

            for rep in self.replacements:
                if rep[0] in self.hosters:
                    self.hosters.remove(rep[0])
                    self.hosters.append(rep[1])

        return self.hosters

    def coreReady(self):

        self.account = self.core.accountManager.getAccountPlugin("RehostTo")

        user = self.account.selectAccount()[0]

        if not user:
            self.log.error("Rehost.to: "+ _("Please add your rehost.to account first and restart pyLoad"))
            return

        data = self.account.getAccountInfo(user)
        self.ses = data["ses"]
        self.long_ses = data["long_ses"]

        pluginMap = {}
        for name in self.core.pluginManager.hosterPlugins.keys():
            pluginMap[name.lower()] = name

        supported = []
        new_supported = []

        for hoster in self.getHostersCached():
            name = removeChars(hoster.lower(), "-.")

            if pluginMap.has_key(name):
                supported.append(pluginMap[name])
            else:
                new_supported.append(hoster)

        module = self.core.pluginManager.getPlugin("RehostTo")
        klass = getattr(module, "RehostTo")
        #inject real debrid plugin
        self.core.log.debug("Rehost.to: Overwritten Hosters: %s" % ", ".join(sorted(supported)))
        for hoster in supported:
            dict = self.core.pluginManager.hosterPlugins[hoster]
            dict["new_module"] = module
            dict["new_name"] = "RehostTo"

        self.core.log.debug("Rehost.to: New Hosters: %s" % ", ".join(sorted(new_supported)))

        #create new regexp
        regexp = r".*(%s).*" % "|".join([klass.__pattern__] + [x.replace(".", "\\.") for x in new_supported])

        dict = self.core.pluginManager.hosterPlugins["RehostTo"]
        dict["pattern"] = regexp
        dict["re"] = re.compile(regexp)