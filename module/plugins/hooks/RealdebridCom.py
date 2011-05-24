# -*- coding: utf-8 -*-
import re

from module.network.RequestFactory import getURL
from module.plugins.Hook import Hook

from module.utils import removeChars

class RealdebridCom(Hook):
    __name__ = "RealdebridCom"
    __version__ = "0.4"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("https", "bool", "Enable HTTPS", "False")]

    __description__ = """Real-Debrid.com hook plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    interval = 0
    hosters = []

    replacements = [("freakshare.net", "freakshare.com")]

    def getHostersCached(self):
        if not self.hosters:
            https = "https" if self.getConfig("https") else "http"
            page = getURL(https + "://real-debrid.com/api/hosters.php")

            self.hosters = [x.strip() for x in page.replace("\"", "").split(",")]

            for rep in self.replacements:
                if rep[0] in self.hosters:
                    self.hosters.remove(rep[0])
                    self.hosters.append(rep[1])

        return self.hosters

    def coreReady(self):
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

        module = self.core.pluginManager.getPlugin("RealdebridCom")
        klass = getattr(module, "RealdebridCom")
        #inject real debrid plugin
        self.core.log.debug("Real-Debrid: Supported Hosters: %s" % ", ".join(sorted(supported)))
        for hoster in supported:
            dict = self.core.pluginManager.hosterPlugins[hoster]
            dict["new_module"] = module
            dict["new_name"] = "RealdebridCom"

        self.core.log.debug("Real-Debrid: New Hosters: %s" % ", ".join(sorted(new_supported)))

        #create new regexp
        regexp = r".*(%s).*" % "|".join([klass.__pattern__] + [x.replace(".", "\\.") for x in new_supported])

        dict = self.core.pluginManager.hosterPlugins["RealdebridCom"]
        dict["pattern"] = regexp
        dict["re"] = re.compile(regexp)
