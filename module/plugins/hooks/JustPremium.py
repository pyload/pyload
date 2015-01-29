# -*- coding: utf-8 -*-

from module.plugins.Hook import Hook


class JustPremium(Hook):
    __name__    = "JustPremium"
    __type__    = "hook"
    __version__ = "0.18"

    __config__ = [("freehosters", "bool", "Allow all freehosters and other unknown sites", False),
                  ("nicehoster" , "str" , "unblock this hosters (comma seperated)"       , "Zippyshare.com")]

    __description__ = """Remove all not premium links from urls added"""
    __license__     = "GPLv3"
    __authors__     = [("mazleu", "mazleica@gmail.com")]


    event_list = ["linksAdded"]


    def coreReady(self) :
        hosts    = ""
        accounts = str(self.core.accountManager.getAccountInfos())

        while "[{" in accounts:
            startid  = accounts.rfind("[], ", 0, accounts.find("[{")) + 2
            endid    = accounts.find("}]", startid) + 2
            hosts    = hosts + "," + accounts[startid+3:accounts.find("'",startid+3)]
            accounts = accounts[0:startid] + accounts[endid:]

        self.hosts    = map(str.strip, (hosts[1:] + "," + self.getConfig("nicehoster")).split(','))
        self.badhosts = map(str.strip, accounts.replace("': [], '",",")[2:-6].split(','))

        self.logDebug("Hosts: %s" % ", ".join(self.hosts))
        self.logDebug("Bad hosts: %s" % ", ".join(self.badhosts))


    def linksAdded(self, links, pid):
        linkdict  = self.core.api.checkURLs(links)

        #: Found at least one hoster with account
        if not any(True for hoster in linkdict if hoster in self.hosts):
            return

        if self.getConfig("freehosters"):
            bad_hosters = [hoster for hoster in linkdict.iterkeys() if hoster in self.badhosts]
        else:
            bad_hosters = [hoster for hoster in linkdict.iterkeys() if hoster not in self.hosts]

        for hoster in bad_hosters:
            self.logInfo(_("Remove links of hoster: %s") % hoster)
            for link in linkdict[hoster]:
                self.logDebug("Remove link: %s" % link)
                links.remove(link)
