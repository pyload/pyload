# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook


class XFileSharingPro(Hook):
    __name__ = "XFileSharingPro"
    __type__ = "hook"
    __version__ = "0.14"

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


    def pluginConfigChanged(self, plugin, name, value):
        if name != "activated":
            self.loadPattern()


    def coreReady(self):
        self.pluginConfigChanged(self.__name__, "coreReady", None)


    def loadPattern(self):
        hoster_list = self.getConfigSet('include_hosters')
        exclude_list = self.getConfigSet('exclude_hosters')

        if self.getConfig("match") != "Listed only":
            if self.getConfig("match") == "Always":
                match_list = ""
            else:
                match_list = '|'.join(sorted(exclude_list))
                self.logDebug("Excluding %d hosters" % len(exclude_list), match_list.replace('|', ', '))

            regexp = r'https?://(?!(?:www\.)?(?:%s))(?:www\.)?([\w^_]+(?:\.[a-zA-Z])+(?:\:\d+)?)/(?:embed-)?\w{12}' % match_list.replace('.', '\.')

        else:
            if self.getConfig('load_default'):
                hoster_list |= set((
                    #WORKING HOSTERS:
                    "eyesfile.co", "eyesfile.com", "fileband.com", "filedwon.com", "hostingbulk.com", "linestorage.com",
                    "ravishare.com", "sharesix.com", "thefile.me", "verzend.be", "xvidstage.com",
                    #NOT TESTED:
                    "101shared.com", "4upfiles.com", "filemaze.ws", "filenuke.com", "linkzhost.com", "mightyupload.com",
                    "rockdizfile.com", "sharebeast.com", "sharerepo.com", "shareswift.com", "uploadbaz.com", "uploadc.com",
                    "vidbull.com", "zalaa.com", "zomgupload.com",
                    #NOT WORKING:
                    "amonshare.com", "banicrazy.info", "boosterking.com", "host4desi.com", "laoupload.com", "rd-fs.com"
                ))

            hoster_list -= (exclude_list)
            hoster_list -= set(('', u''))

            if not hoster_list:
                self.unload()
                return

            match_list = '|'.join(sorted(hoster_list))
            regexp = r'https?://(?:[^/]*\.)?(%s)/(?:embed-)?\w{12}' % match_list.replace('.', '\.')
            self.logDebug("Handling %d hosters" % len(hoster_list), match_list.replace('|', ', '))

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
