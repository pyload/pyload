# -*- coding: utf-8 -*-
import re

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class Vipleech4uCom(MultiHoster):
    __name__ = "Vipleech4uCom"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """Vipleech4u.com hook plugin"""
    __author_name__ = ("Kagenoshin")
    __author_mail__ = ("kagenoshin@gmx.ch")

    HOSTER_PATTERN = re.compile(r'align\s*?=\s*?["\']*?left.*?<\s*?strong\s*?>([^<]*?)<', re.I)

    def getHoster(self):
        hosters = {
            'depositfiles': ['depositfiles.com', 'dfiles.eu'],
            'uploaded': ['uploaded.to', 'uploaded.net', 'ul.to'],
            'rapidggator': ['rapidgator.net'],  # they have a typo it's called rapidgator
            'freakshare': ['freakshare.net', 'freakshare.com'],
            'filefactory': ['filefactory.com'],
            'bitshare': ['bitshare.com'],
            'share-online': ['share-online.biz', 'egoshare.com'],
            'youtube': ['youtube.com'],
            'turbobit': ['turbobit.net', 'unextfiles.com'],
            'firedrive': ['firedrive.com', 'putlocker.com'],
            'filepost': ['filepost.com', 'fp.io'],
            'netload': ['netload.in'],
            'uploadhero': ['uploadhero.com'],
            'ryushare': ['ryushare.com'],
        }

        #check if the list is still valid
        self.check_for_new_or_removed_hosters(hosters)

        #build list
        hoster_list = []

        for item in hosters.itervalues():
            hoster_list.extend(item)

        return hoster_list

    def check_for_new_or_removed_hosters(self, hosters):
        #get the old hosters
        old_hosters = hosters.keys()

        #load the current hosters from vipleech4u.com
        page = getURL('http://vipleech4u.com/hosts.php')
        current_hosters = self.HOSTER_PATTERN.findall(page)
        current_hosters = [x.lower() for x in current_hosters]

        #let's look for new hosters
        new_hosters = []

        for hoster in current_hosters:
            if not hoster in old_hosters:
                new_hosters.append(hoster)

        #let's look for removed hosters
        removed_hosters = []

        for hoster in old_hosters:
            if not hoster in current_hosters:
                removed_hosters.append(hoster)

        if new_hosters:
            self.logDebug('The following new hosters were found on vipleech4u.com: %s' % str(new_hosters))

        if removed_hosters:
            self.logDebug('The following hosters were removed from vipleech4u.com: %s' % str(removed_hosters))

        if not (new_hosters and removed_hosters):
            self.logDebug('The hoster list is still valid.')
