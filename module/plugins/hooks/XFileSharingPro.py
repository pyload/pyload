# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook


class XFileSharingPro(Hook):
    __name__    = "XFileSharingPro"
    __type__    = "hook"
    __version__ = "0.20"

    __config__ = [("activated", "bool", "Activated", True),
                  ("every_hoster", "bool", "Try to hook any hoster", True),
                  ("every_crypter", "bool", "Try to hook any crypter", True),
                  ("load_default", "bool", "Load built-in plugins", True),
                  ("hoster_list", "str", "Load hosters (comma separated)", ""),
                  ("crypter_list", "str", "Load crypters (comma separated)", "")]

    __description__ = """Load XFileSharingPro based hosters and crypter which don't need a own plugin to run"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]
    regex = {'hoster' : (r'https?://(?:www\.)?([\w^_]+(?:\.[a-zA-Z]{2,})+(?:\:\d+)?)/(?:embed-)?\w{12}',
                         r'https?://(?:[^/]+\.)?(%s)/(?:embed-)?\w{12}\W?'),
             'crypter': (r'https?://(?:www\.)?([\w^_]+(?:\.[a-zA-Z]{2,})+(?:\:\d+)?)/(?:user|folder)s?/\w+',
                         r'https?://(?:[^/]+\.)?(%s)/(?:user|folder)s?/\w+')}

    HOSTER_LIST = [#WORKING HOSTERS:
                   "eyesfile.ca", "file4safe.com", "fileband.com", "filedwon.com", "filevice.com", "hostingbulk.com",
                   "linestorage.com", "ravishare.com", "sharesix.com", "thefile.me", "verzend.be", "xvidstage.com",
                   #NOT TESTED:
                   "101shared.com", "4upfiles.com", "filemaze.ws", "filenuke.com", "linkzhost.com", "mightyupload.com",
                   "rockdizfile.com", "sharebeast.com", "sharerepo.com", "shareswift.com", "uploadbaz.com", "uploadc.com",
                   "vidbull.com", "zalaa.com", "zomgupload.com",
                   #NOT WORKING:
                   "amonshare.com", "banicrazy.info", "boosterking.com", "host4desi.com", "laoupload.com", "rd-fs.com"]
    CRYPTER_LIST = []


    # def pluginConfigChanged(self, plugin, name, value):
        # self.loadPattern()


    def coreReady(self):
        self.loadPattern()


    def loadPattern(self):
        for type, plugin in (("hoster", "XFileSharingPro"), ("crypter", "XFileSharingProFolder")):
            every_plugin = self.getConfig('every_%s' % type)

            if every_plugin:
                regexp = self.regex[type][0]
            else:
                s = self.getConfig('%s_list' % type).replace('\\', '').replace('|', ',').replace(';', ',').lower()
                plugin_list = set([x.strip() for x in s.split(',')])

                if self.getConfig('load_default'):
                    plugin_list |= set([x.lower() for x in getattr(self, "%s_LIST" % type.upper())])

                plugin_list -= set(('', u''))

                if not plugin_list:
                    self.unload()
                    return

                match_list = '|'.join(sorted(plugin_list))
                self.logInfo("Handling %d %ss: %s" % (len(plugin_list), type, match_list.replace('|', ', ')))

                regexp = self.regex[type][1] % match_list  #.replace('.', '\.')

            dict = self.core.pluginManager.plugins[type][plugin]
            dict['pattern'] = regexp
            dict['re'] = re.compile(regexp)

            self.logDebug("Loaded %s regex: `%s`" % (type, regexp))


    def unload(self):
        regexp = r'^unmatchable$'
        for type, plugin in (("hoster", "XFileSharingPro"), ("crypter", "XFileSharingProFolder")):
            dict = self.core.pluginManager.plugins[type][plugin]
            dict['pattern'] = regexp
            dict['re'] = re.compile(regexp)
