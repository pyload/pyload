# -*- coding: utf-8 -*-

import re

from pyload.plugin.Addon import Addon


class JustPremium(Addon):
    __name__    = "JustPremium"
    __type__    = "addon"
    __version__ = "0.22"

    __config__ = [("excluded", "str", "Exclude hosters (comma separated)", ""),
                  ("included", "str", "Include hosters (comma separated)", "")]

    __description__ = """Remove not-premium links from added urls"""
    __license__     = "GPLv3"
    __authors__     = [("mazleu"        , "mazleica@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com" ),
                       ("immenz"        , "immenz@gmx.net"    )]


    event_list = ["linksAdded"]
    interval   = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def linksAdded(self, links, pid):
        hosterdict = self.core.pluginManager.hosterPlugins
        linkdict   = self.core.api.checkURLs(links)

        premiumplugins = set(account.type for account in self.core.api.getAccounts(False) \
                             if account.valid and account.premium)
        multihosters   = set(hoster for hoster in self.core.pluginManager.hosterPlugins \
                             if 'new_name' in hosterdict[hoster] \
                             and hosterdict[hoster]['new_name'] in premiumplugins)

        excluded = map(lambda domain: "".join(part.capitalize() for part in re.split(r'(\.|\d+)', domain) if part != '.'),
                       self.getConfig('excluded').replace(' ', '').replace(',', '|').replace(';', '|').split('|'))
        included = map(lambda domain: "".join(part.capitalize() for part in re.split(r'(\.|\d+)', domain) if part != '.'),
                       self.getConfig('included').replace(' ', '').replace(',', '|').replace(';', '|').split('|'))

        hosterlist = (premiumplugins | multihosters).union(excluded).difference(included)

        #: Found at least one hoster with account or multihoster
        if not any( True for pluginname in linkdict if pluginname in hosterlist ):
            return

        for pluginname in set(linkdict.keys()) - hosterlist:
            self.logInfo(_("Remove links of plugin: %s") % pluginname)
            for link in linkdict[pluginname]:
                self.logDebug("Remove link: %s" % link)
                links.remove(link)
