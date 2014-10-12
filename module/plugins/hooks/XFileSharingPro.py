# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook


class XFileSharingPro(Hook):
    __name__ = "XFileSharingPro"
    __type__ = "hook"
    __version__ = "0.15"

    __config__ = [("activated", "bool", "Activated", True),
                  ("match", "Always;Always except excluded;Listed only", "Match", "Always except excluded"),
                  ("load_default", "bool", "Include built-in hoster list", True),
                  ("include_hosters", "str", "Include hosters (comma separated)", ""),
                  ("exclude_hosters", "str", "Exclude hosters (comma separated)", "")]

    __description__ = """XFileSharingPro hook plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["pluginConfigChanged"]

    HOSTER_LIST = [#WORKING HOSTERS:
                   "eyesfile.co", "eyesfile.com", "fileband.com", "filedwon.com", "hostingbulk.com", "linestorage.com",
                   "ravishare.com", "sharesix.com", "thefile.me", "verzend.be", "xvidstage.com",
                   #NOT TESTED:
                   "101shared.com", "4upfiles.com", "filemaze.ws", "filenuke.com", "linkzhost.com", "mightyupload.com",
                   "rockdizfile.com", "sharebeast.com", "sharerepo.com", "shareswift.com", "uploadbaz.com", "uploadc.com",
                   "vidbull.com", "zalaa.com", "zomgupload.com",
                   #NOT WORKING:
                   "amonshare.com", "banicrazy.info", "boosterking.com", "host4desi.com", "laoupload.com", "rd-fs.com"]


    def pluginConfigChanged(self, plugin, name, value):
        if name != "activated":
            self.loadPattern()


    def coreReady(self):
        self.loadPattern()


    def loadPattern(self):
        include_hosters = self.getConfigSet('include_hosters')
        exclude_hosters = self.getConfigSet('exclude_hosters')

        if self.getConfig("match") != "Listed only":
            if self.getConfig("match") == "Always":
                match_list = ""
            else:
                hoster_list = exclude_hosters - set(('', u''))
                match_list = '|'.join(sorted(hoster_list))
                self.logDebug("Excluding %d hosters" % len(hoster_list), match_list.replace('|', ', '))

            regexp = r'https?://(?!(?:www\.)?(?:%s))(?:www\.)?([\w^_]+(?:\.[a-zA-Z]{2,})+(?:\:\d+)?)/(?:embed-)?\w{12}' % match_list.replace('.', '\.')

        else:
            hoster_list = include_hosters

            if self.getConfig('load_default'):
                hoster_list |= set(self.HOSTER_LIST)

            hoster_list -= exclude_hosters
            hoster_list -= set(('', u''))

            if not hoster_list:
                self.unload()
                return

            match_list = '|'.join(sorted(hoster_list))
            self.logDebug("Handling %d hosters" % len(hoster_list), match_list.replace('|', ', '))

            regexp = r'https?://(?:[^/]*\.)?(%s)/(?:embed-)?\w{12}' % match_list.replace('.', '\.')

        dict = self.core.pluginManager.hosterPlugins['XFileSharingPro']
        dict['pattern'] = regexp
        dict['re'] = re.compile(regexp)
        self.logDebug("Pattern loaded")


    def getConfigSet(self, option):
        s = self.getConfig(option).lower().replace('|', ',').replace(';', ',')
        return set([x.strip() for x in s.split(',')])


    def unload(self):
        regexp = r'^unmatchable$'
        dict = self.core.pluginManager.hosterPlugins['XFileSharingPro']
        dict['pattern'] = regexp
        dict['re'] = re.compile(regexp)
