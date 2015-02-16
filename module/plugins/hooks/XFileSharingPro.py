# -*- coding: utf-8 -*-

import re

from pyload.plugin.Addon import Addon


class XFileSharingPro(Addon):
    __name__    = "XFileSharingPro"
    __type__    = "hook"
    __version__ = "0.26"

    __config__ = [("activated"       , "bool", "Activated"                     , True ),
                ("use_hoster_list" , "bool", "Load listed hosters only"      , True ),
                ("use_crypter_list", "bool", "Load listed crypters only"     , False),
                ("use_builtin_list", "bool", "Load built-in plugin list"     , True ),
                ("hoster_list"     , "str" , "Hoster list (comma separated)" , ""   ),
                ("crypter_list"    , "str" , "Crypter list (comma separated)", ""   )]

    __description__ = """Load XFileSharingPro based hosters and crypter which don't need a own plugin to run"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]
    regexp = {'hoster' : (r'https?://(?:www\.)?([\w.^_]+(?:\.[a-zA-Z]{2,})(?:\:\d+)?)/(?:embed-)?\w{12}(?:\W|$)',
                          r'https?://(?:[^/]+\.)?(%s)/(?:embed-)?\w+'),
              'crypter': (r'https?://(?:www\.)?([\w.^_]+(?:\.[a-zA-Z]{2,})(?:\:\d+)?)/(?:user|folder)s?/\w+',
                          r'https?://(?:[^/]+\.)?(%s)/(?:user|folder)s?/\w+')}

    HOSTER_LIST  = [#WORKING HOSTERS:
                    "eyesfile.ca", "file4safe.com", "fileband.com", "filedwon.com", "filevice.com", "hostingbulk.com",
                    "linestorage.com", "ravishare.com", "sharesix.com", "thefile.me", "verzend.be", "xvidstage.com",
                    #NOT TESTED:
                    "101shared.com", "4upfiles.com", "filemaze.ws", "filenuke.com", "linkzhost.com", "mightyupload.com",
                    "rockdizfile.com", "sharebeast.com", "sharerepo.com", "shareswift.com", "uploadbaz.com", "uploadc.com",
                    "vidbull.com", "zalaa.com", "zomgupload.com",
                    #NOT WORKING:
                    "amonshare.com", "banicrazy.info", "boosterking.com", "host4desi.com", "laoupload.com", "rd-fs.com"]
    CRYPTER_LIST = []


    # def pluginConfigChanged(self.__name__, plugin, name, value):
        # self.loadPattern()


    def activate(self):
        self.loadPattern()


    def loadPattern(self):
        use_builtin_list = self.getConfig('use_builtin_list')

        for type in ("hoster", "crypter"):
            every_plugin = not self.getConfig("use_%s_list" % type)

            if every_plugin:
                self.logInfo(_("Handling any %s I can!") % type)
                pattern = self.regexp[type][0]
            else:
                s = self.getConfig('%s_list' % type).replace('\\', '').replace('|', ',').replace(';', ',').lower()
                plugin_list = set([x.strip() for x in s.split(',')])

                if use_builtin_list:
                    plugin_list |= set([x.lower() for x in getattr(self, "%s_LIST" % type.upper())])

                plugin_list -= set(('', u''))

                if not plugin_list:
                    self.logInfo(_("No %s to handle") % type)
                    self._unload(type)
                    return

                match_list = '|'.join(sorted(plugin_list))

                len_match_list = len(plugin_list)
                self.logInfo(_("Handling %d %s%s: %s") % (len_match_list,  type, "" if len_match_list is 1 else "s", match_list.replace('|', ', ')))

                pattern = self.regexp[type][1] % match_list.replace('.', '\.')

            dict = self.core.pluginManager.plugins[type]["XFileSharingPro"]
            dict['pattern'] = pattern
            dict['re'] = re.compile(pattern)

            self.logDebug("Loaded %s pattern: %s" % (type, pattern))


    def _unload(self, type):
        dict = self.core.pluginManager.plugins[type]["XFileSharingPro"]
        dict['pattern'] = r'^unmatchable$'
        dict['re'] = re.compile(dict['pattern'])


    def deactivate(self):
        for type in ("hoster", "crypter"):
            self._unload(type, "XFileSharingPro")
