# -*- coding: utf-8 -*-
#@author: mkaay

from __future__ import unicode_literals
from time import mktime, time

import feedparser

from pyload.plugin.hook import Hook


class Ev0InFetcher(Hook):
    __name__ = "Ev0InFetcher"
    __version__ = "0.21"
    __description__ = """Checks rss feeds for Ev0.in"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("interval", "int", "Check interval in minutes", 10),
                  ("queue", "bool", "Move new shows directly to Queue", False),
                  ("shows", "str", "Shows to check for (comma seperated)", ""),
                  ("quality", "xvid;x264;rmvb", "Video Format", "xvid"),
                  ("hoster", "str", "Hoster to use (comma seperated)",
                   "NetloadIn,RapidshareCom,MegauploadCom,HotfileCom")]
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"

    def setup(self):
        self.interval = self.get_config("interval") * 60

    def filter_links(self, links):
        results = self.pyload.pluginmanager.parse_urls(links)
        sortedLinks = {}

        for url, hoster in results:
            if hoster not in sortedLinks:
                sortedLinks[hoster] = []
            sortedLinks[hoster].append(url)

        for h in self.get_config("hoster").split(","):
            try:
                return sortedLinks[h.strip()]
            except Exception:
                continue
        return []

    def periodical(self):
        def normalizefiletitle(filename):
            filename = filename.replace('.', ' ')
            filename = filename.replace('_', ' ')
            filename = filename.lower()
            return filename

        shows = [s.strip() for s in self.get_config("shows").split(",")]

        feed = feedparser.parse("http://feeds.feedburner.com/ev0in/%s?format=xml" % self.get_config("quality"))

        showStorage = {}
        for show in shows:
            showStorage[show] = int(self.get_storage("show_%s_lastfound" % show, 0))

        found = False
        for item in feed['items']:
            for show, lastfound in showStorage.items():
                if show.lower() in normalizefiletitle(item['title']) and lastfound < int(mktime(item.date_parsed)):
                    links = self.filter_links(item['description'].split("<br />"))
                    packagename = item['title'].encode("utf-8")
                    self.log_info("Ev0InFetcher: new episode '%s' (matched '%s')" % (packagename, show))
                    self.pyload.api.add_package(packagename, links, 1 if self.get_config("queue") else 0)
                    self.set_storage("show_%s_lastfound" % show, int(mktime(item.date_parsed)))
                    found = True
        if not found:
            #self.log_debug("Ev0InFetcher: no new episodes found")
            pass

        for show, lastfound in self.get_storage().items():
            if int(lastfound) > 0 and int(lastfound) + (3600 * 24 * 30) < int(time()):
                self.del_storage("show_%s_lastfound" % show)
                self.log_debug("Ev0InFetcher: cleaned '%s' record" % show)
