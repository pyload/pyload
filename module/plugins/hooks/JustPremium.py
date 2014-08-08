# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mazleu
"""
from module.plugins.Hook import Hook
from module.plugins.Account import Account
from module.plugins.Hoster import Hoster


class JustPremium(Hook):
    __name__ = "JustPremium"
    __version__ = "0.16"
    __description__ = "If you add multiple links with at least one premium hoster link, all non premium links get removed"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("freehosters","bool", "Allow all freehosters and other unknown sites", "false"),
                  ("nicehoster", "str", "unblock this hosters (comma seperated)", "Zippyshare.com")]

    __author_name__ = ("mazleu")
    __author_mail__ = ("mazleica@gmail.com")

    event_list = ["linksAdded"]

    def coreReady(self) :
        accs=str(self.core.accountManager.getAccountInfos())
        global badhosts
        global hosts
        hosts = ""
        while "[{" in accs:
            startid=accs.rfind("[], ", 0, accs.find("[{"))+2
            endid=accs.find("}]",startid)+2
            hosts=hosts+","+accs[startid+3:accs.find("'",startid+3)]
            accs=accs[0:startid]+accs[endid:]
        badhosts=accs.replace("': [], '",",")[2:-6]
        hosts=hosts[1:]
        hosts=hosts+","+self.getConfig("nicehoster")
        self.logDebug("good hosts:",hosts)
        self.logDebug("bad hosts:",badhosts)


    def filterLinks(self, t):
        links = self.core.api.checkURLs(t)
        hosterlist =""
        bhosters = [x.strip() for x in badhosts.split(",")]
        ghosters = [x.strip() for x in hosts.split(",")]
        premhoster = False
        for hoster in links:
            self.logDebug(hoster)
            if hoster in ghosters:
                premhoster = True
                self.logDebug ("Found at least one hoster with account")
        if premhoster :
            for hoster in links:
                if self.getConfig("freehosters"):
                    if hoster in bhosters:
                        self.logInfo("remove links from hoster '%s' " % (hoster))
                        for link in links[hoster]:
                            t.remove(link)
                            self.logDebug("remove link '%s'because hoster was: '%s' " % (link,hoster))
                else:
                    if not hoster in ghosters:
                        self.logInfo("remove links from hoster '%s' " % (hoster))
                        for link in links[hoster]:
                            t.remove(link)
                            self.logDebug("remove link '%s' because hoster was: '%s' " % (link,hoster))
    def linksAdded(self, links, pid):
        self.filterLinks(links)
