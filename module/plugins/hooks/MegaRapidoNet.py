# -*- coding: utf-8 -*-
import re

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class MegaRapidoNet(MultiHoster):
    __name__ = "MegaRapidoNet"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """Megarapido.net hook plugin"""
    __author_name__ = ("Kagenoshin")
    __author_mail__ = ("kagenoshin@gmx.ch")

    HOSTER_PATTERN = re.compile(r'align\s*?=\s*?["\']*?left.*?<\s*?strong\s*?>([^<]*?)<', re.I)

    def getHoster(self):
        hosters = {
            '1fichier': [],#leave it there are so many possible addresses?
            '1st-files': ['1st-files.com'],
            '2shared': ['2shared.com'],
            '4shared': ['4shared.com', '4shared-china.com'],
            'asfile': ['http://asfile.com/'],
            'bitshare': ['bitshare.com'],
            'brupload': ['brupload.net'],
            'crocko': ['crocko.com','easy-share.com'],
            'dailymotion': ['dailymotion.com'],
            'depfile': ['depfile.com'],
            'depositfiles': ['depositfiles.com', 'dfiles.eu'],
            'dizzcloud': ['dizzcloud.com'],
            'dl.dropbox': [],
            'extabit': ['extabit.com'],
            'extmatrix': ['extmatrix.com'],
            'facebook': [],
            'file4go': ['file4go.com'],
            'filecloud': ['filecloud.io','ifile.it','mihd.net'],
            'filefactory': ['filefactory.com'],
            'fileom': ['fileom.com'],
            'fileparadox': ['fileparadox.in'],
            'filepost': ['filepost.com', 'fp.io'],
            'filerio': ['filerio.in','filerio.com','filekeen.com'],
            'filesflash': ['filesflash.com'],
            'firedrive': ['firedrive.com', 'putlocker.com'],
            'flashx': [],
            'freakshare': ['freakshare.net', 'freakshare.com'],
            'gigasize': ['gigasize.com'],
            'hipfile': ['hipfile.com'],
            'junocloud': ['junocloud.me'],
            'letitbit': ['letitbit.net','shareflare.net'],
            'mediafire': ['mediafire.com'],
            'mega': ['mega.co.nz'],
            'megashares': ['megashares.com'],
            'metacafe': ['metacafe.com'],
            'netload': ['netload.in'],
            'oboom': ['oboom.com'],
            'rapidgator': ['rapidgator.net'],
            'rapidshare': ['rapidshare.com'],
            'rarefile': ['rarefile.net'],
            'ryushare': ['ryushare.com'],
            'sendspace': ['sendspace.com'],
            'turbobit': ['turbobit.net', 'unextfiles.com'],
            'uploadable': ['uploadable.ch'],
            'uploadbaz': ['uploadbaz.com'],
            'uploaded': ['uploaded.to', 'uploaded.net', 'ul.to'],
            'uploadhero': ['uploadhero.com'],
            'uploading': ['uploading.com'],
            'uptobox': ['uptobox.com'],
            'xvideos': ['xvideos.com'],
            'youtube': ['youtube.com']
        }

        #check if the list is still valid
        #has to be added! self.check_for_new_or_removed_hosters(hosters)

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
