# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook


class XFileSharingPro(Hook):
    __name__ = "XFileSharingPro"
    __type__ = "hook"
    __version__ = "0.16"

    __config__ = [("activated", "bool", "Activated", True),
                  ("match_hoster", "Always;Always except excluded;Listed only", "Hoster match", "Always except excluded"),
                  ("match_crypter", "Always;Always except excluded;Listed only", "Crypter match", "Always except excluded"),
                  ("load_default", "bool", "Include built-in lists", True),
                  ("include_hosters", "str", "Include hosters (comma separated)", ""),
                  ("exclude_hosters", "str", "Exclude hosters (comma separated)", ""),
                  ("include_crypters", "str", "Include crypters (comma separated)", ""),
                  ("exclude_crypters", "str", "Exclude crypters (comma separated)", "")]

    __description__ = """Load hosters and crypter, based upon XFileSharingPro, which don't need a own plugin to work fine"""
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
    CRYPTER_LIST = []


    def pluginConfigChanged(self, plugin, name, value):
        if name != "activated":
            self.loadPattern()


    def coreReady(self):
        self.loadPattern()


    def loadPattern(self):
        regex = {'hoster'  = (r'https?://(?!(?:www\.)?(?:%s))(?:www\.)?([\w^_]+(?:\.[a-zA-Z]{2,})+(?:\:\d+)?)/(?:embed-)?\w{12}',
                              r'https?://(?:[^/]+\.)?(%s)/(?:embed-)?\w{12}'),
                 'crypter' = (r'https?://(?!(?:www\.)?(?:%s))(?:www\.)?([\w^_]+(?:\.[a-zA-Z]{2,})+(?:\:\d+)?)/(?:user|folder)s?/\w+',
                              r'https?://(?:[^/]+\.)?(%s)/(?:user|folder)s?/\w+')}

        for type, plugin in (("hoster", "XFileSharingPro"), ("crypter", "XFileSharingProFolder")):
            match = self.getConfig('match_%ss' % type)
            include_set = self.getConfigSet('include_%ss' % type)
            exclude_set = self.getConfigSet('exclude_%ss' % type)

            if match != "Listed only":
                if match == "Always":
                    match_list = ""
                else:
                    hoster_list = exclude_set - set(('', u''))
                    match_list = '|'.join(sorted(hoster_list))
                    self.logDebug("Excluding %d %ss" % (len(hoster_list), type), match_list.replace('|', ', '))

                regexp = regex[type][0] % match_list.replace('.', '\.')

            else:
                hoster_list = include_set

                if self.getConfig('load_default'):
                    hoster_list |= set(getattr(self, "%s_LIST" % type.upper()))

                hoster_list -= exclude_set
                hoster_list -= set(('', u''))

                if not hoster_list:
                    self.unload()
                    return

                match_list = '|'.join(sorted(hoster_list))
                self.logDebug("Handling %d %ss" % (len(hoster_list), type), match_list.replace('|', ', '))

                regexp = regex[type][1] % match_list.replace('.', '\.')

            dict = self.core.pluginManager.plugins[type][plugin]
            dict['pattern'] = regexp
            dict['re'] = re.compile(regexp)
            self.logDebug("Pattern loaded for %ss" % type)


    def getConfigSet(self, option):
        s = self.getConfig(option).lower().replace('|', ',').replace(';', ',')
        return set([x.strip() for x in s.split(',')])


    def unload(self):
        regexp = r'^unmatchable$'
        for type, plugin in (("hoster", "XFileSharingPro"), ("crypter", "XFileSharingProFolder")):
            dict = self.core.pluginManager.plugins[type][plugin]
            dict['pattern'] = regexp
            dict['re'] = re.compile(regexp)
