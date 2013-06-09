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

from module.plugins.Addon import Addon

class Ev0InFetcher(Addon):
    __name__ = "Ev0InFetcher"
    __version__ = "0.2"
    __description__ = """checks rss feeds for ev0.in"""
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("interval", "int", "Check interval in minutes", "10"),
                  ("queue", "bool", "Move new shows directly to Queue", False),
                  ("shows", "str", "Shows to check for (comma separated)", ""),
                  ("quality", "xvid;x264;rmvb", "Video Format", "xvid"),
                  ("hoster", "str", "Hoster to use (comma separated)", "NetloadIn,RapidshareCom,MegauploadCom,HotfileCom")]
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")

    def setup(self):
        self.interval = self.getConfig("interval") * 60

    def filterLinks(self, links):
        results = self.core.pluginManager.parseUrls(links)
        sortedLinks = {}
        
        for url, hoster in results[0]:
            if hoster not in sortedLinks:
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

        showStorage = {}
        for show in shows:
            showStorage[show] = int(self.getStorage("show_%s_lastfound" % show, 0))
        
        found = False
        for item in feed['items']:
            for show, lastfound in showStorage.iteritems():
                if show.lower() in normalizefiletitle(item['title']) and lastfound < int(mktime(item.date_parsed)):
                    links = self.filterLinks(item['description'].split("<br />"))
                    packagename = item['title'].encode("utf-8")
                    self.core.log.info("Ev0InFetcher: new episode '%s' (matched '%s')" % (packagename, show))
                    self.core.api.addPackage(packagename, links, 1 if self.getConfig("queue") else 0)
                    self.setStorage("show_%s_lastfound" % show, int(mktime(item.date_parsed)))
                    found = True
        if not found:
            #self.core.log.debug("Ev0InFetcher: no new episodes found")
            pass

        for show, lastfound in self.getStorage().iteritems():
            if int(lastfound) > 0 and int(lastfound) + (3600*24*30) < int(time()):
                self.delStorage("show_%s_lastfound" % show)
                self.core.log.debug("Ev0InFetcher: cleaned '%s' record" % show)
