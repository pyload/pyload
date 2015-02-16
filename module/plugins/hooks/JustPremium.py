# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook


class JustPremium(Hook):
    __name__    = "JustPremium"
    __type__    = "hook"
    __version__ = "0.21"

    __config__ = [("excluded", "str", "Exclude hosters (comma separated)", "")]

    __description__ = """Remove all not premium links from urls added"""
    __license__     = "GPLv3"
    __authors__     = [("mazleu", "mazleica@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("immenz", "immenz@gmx.net")]


    event_list = ["linksAdded"]


    def linksAdded(self, links, pid):
        hosterdict = self.core.pluginManager.hosterPlugins
        linkdict   = self.core.api.checkURLs(links)

        premiumplugins = set(account.type for account in self.core.api.getAccounts(False) \
                             if account.valid and account.premium)
        multihosters   = set(hoster for hoster in self.core.pluginManager.hosterPlugins \
                             if 'new_name' in hosterdict[hoster] \
                             and hosterdict[hoster]['new_name'] in premiumplugins)

        #: Found at least one hoster with account or multihoster
        if not any(True for pluginname in linkdict if pluginname in premiumplugins | multihosters):
            return

        excluded = map(lambda domain: "".join(part.capitalize() for part in re.split(r'(\.|\d+)', domain) if part != '.'),
                       self.getConfig('excluded').replace(' ', '').replace(',', '|').replace(';', '|').split('|'))

        for pluginname in set(linkdict.keys()) - (premiumplugins | multihosters).union(excluded):
            self.logInfo(_("Remove links of plugin: %s") % pluginname)
            for link in linkdict[pluginname]:
                self.logDebug("Remove link: %s" % link)
                links.remove(link)
