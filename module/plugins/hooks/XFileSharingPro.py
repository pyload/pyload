# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook


class XFileSharingPro(Hook):
    __name__ = "XFileSharingPro"
    __type__ = "hook"
    __version__ = "0.13"

    __config__ = [("activated", "bool", "Activated", True),
                  ("load_default", "bool", "Include default (built-in) hoster list", True),
                  ("include_hosters", "str", "Include hosters (comma separated)", ""),
                  ("exclude_hosters", "str", "Exclude hosters (comma separated)", "")]

    __description__ = """XFileSharingPro hook plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    def coreReady(self):
        self.loadPattern()


    def loadPattern(self):
        hoster_list = self.getConfigSet('include_hosters')
        exclude_list = self.getConfigSet('exclude_hosters')

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

        regexp = r'http://(?:[^/]*\.)?(%s)/(?:embed-)?\w{12}' % ('|'.join(sorted(hoster_list)).replace('.', '\.'))

        dict = self.core.pluginManager.hosterPlugins['XFileSharingPro']
        dict['pattern'] = regexp
        dict['re'] = re.compile(regexp)
        self.logDebug("Pattern loaded - handling %d hosters" % len(hoster_list))


    def getConfigSet(self, option):
        s = self.getConfig(option).lower().replace('|', ',').replace(';', ',')
        return set([x.strip() for x in s.split(',')])


    def unload(self):
        dict = self.core.pluginManager.hosterPlugins['XFileSharingPro']
        dict['pattern'] = r'^unmatchable$'
        dict['re'] = re.compile(r'^unmatchable$')
