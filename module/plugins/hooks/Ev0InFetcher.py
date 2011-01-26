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

    @author: mkaay
"""
from module.lib import feedparser
from time import mktime, time

from module.plugins.Hook import Hook
from module.plugins.PluginStorage import PluginStorage

class Ev0InFetcher(Hook, PluginStorage):
    __name__ = "Ev0InFetcher"
    __version__ = "0.1"
    __description__ = """checks rss feeds for ev0.in"""
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("interval", "int", "Check interval in minutes", "10"),
                  ("queue", "bool", "Move new shows directly to Queue", False),
                  ("shows", "str", "Shows to check for (comma seperated)", ""),
                  ("quality", "str", "xvid/x264/rmvb", "xvid"),
                  ("hoster", "str", "Hoster to use (comma seperated)", "NetloadIn,RapidshareCom,MegauploadCom,HotfileCom")]
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")

    def setup(self):
        self.interval = self.getConfig("interval") * 60
    
    def filterLinks(self, links):
        results = self.core.pluginManager.parseUrls(links)
        sortedLinks = {}
        
        for url, hoster in results:
            if not sortedLinks.has_key(hoster):
                sortedLinks[hoster] = []
            sortedLinks[hoster].append(url)
        
        for h in self.getConfig("hoster").split(","):
            try:
                return sortedLinks[h.strip()]
            except:
                continue
        return []
    
    def periodical(self):
        def normalizefiletitle(filename):
            filename = filename.replace('.', ' ')
            filename = filename.replace('_', ' ')
            filename = filename.lower()
            return filename
        
        shows = [s.strip() for s in self.getConfig("shows").split(",")]
        
        feed = feedparser.parse("http://feeds.feedburner.com/ev0in/%s?format=xml" % self.getConfig("quality"))
        currentTime = time()
        lastCheck = int(self.getStorage("last_check", 0))
        
        for item in feed['items']: 
            if mktime(item.date_parsed) > lastCheck:
                for x in shows: 
                    if x.lower() in normalizefiletitle(item['title']):
                        links = self.filterLinks(item['description'].split("<br />"))
                        packagename = item['title'].encode("utf-8")
                        self.core.log.debug("Ev0InFetcher: new episode %s" % packagename)
                        self.core.server_methods.add_package(packagename, links, queue=(1 if self.getConfig("queue") else 0))
        self.setStorage("last_check", int(currentTime))
        
