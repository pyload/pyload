# -*- coding: utf-8 -*-

from module.plugins.Hook import Hook


class JustPremium(Hook):
    __name__    = "JustPremium"
    __type__    = "hook"
    __version__ = "0.20"

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

        self.hosts    = map(lambda x: x.strip(), (hosts[1:] + "," + self.getConfig("nicehoster")).replace('.','').split(','))
        self.badhosts = map(lambda x: x.strip(), accounts.replace("': [], '",",")[2:-6].split(','))

        self.logDebug("Hosts: %s" % ", ".join(self.hosts))
        self.logDebug("Bad hosts: %s" % ", ".join(self.badhosts))


    def linksAdded(self, links, pid):
        linkdict  = self.core.api.checkURLs(links)
       
        # Check if Multihoster has overwritten Hoster-Plugins
        multi_hosts = [hoster for hoster in self.core.pluginManager.hosterPlugins if 'new_name' in self.core.pluginManager.hosterPlugins[hoster]]
        if multi_hosts:
            self.logDebug("Hosts extended via Multihoster: %s" % ", ".join(multi_hosts + self.hosts))
        
        #: Found at least one hoster with account or multihoster
        if not any(True for hoster in linkdict if hoster in set(multi_hosts + self.hosts)):
            return

        if self.getConfig("freehosters"):
            bad_hosters = [hoster for hoster in linkdict.iterkeys() if hoster in set(self.badhosts) - set(multi_hosts)]
        else:
            bad_hosters = [hoster for hoster in linkdict.iterkeys() if hoster not in set(multi_hosts + self.hosts)]

        for hoster in bad_hosters:
            self.logInfo(_("Remove links of hoster: %s") % hoster)
            for link in linkdict[hoster]:
                self.logDebug("Remove link: %s" % link)
                links.remove(link)
