# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Hook import Hook


class XFileSharingPro(Hook):
    __name__    = "XFileSharingPro"
    __type__    = "hook"
    __version__ = "0.42"
    __status__  = "testing"

    __config__ = [("activated"       , "bool", "Activated"                     , True ),
                  ("use_hoster_list" , "bool", "Load listed hosters only"      , False),
                  ("use_crypter_list", "bool", "Load listed crypters only"     , False),
                  ("use_builtin_list", "bool", "Load built-in plugin list"     , True ),
                  ("hoster_list"     , "str" , "Hoster list (comma separated)" , ""   ),
                  ("crypter_list"    , "str" , "Crypter list (comma separated)", ""   )]

    __description__ = """Load XFileSharingPro based hosters and crypters which don't need a own plugin to run"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    regexp     = {'hoster' : (r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/(?:embed-)?\w{12}(?:\W|$)',
                              r'https?://(?:[^/]+\.)?(?P<DOMAIN>%s)/(?:embed-)?\w+'),
                  'crypter': (r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/(?:user|folder)s?/\w+',
                              r'https?://(?:[^/]+\.)?(?P<DOMAIN>%s)/(?:user|folder)s?/\w+')}

    HOSTER_BUILTIN  = [#WORKING HOSTERS:
                       "ani-stream.com", "backin.net", "cloudsix.me", "eyesfile.ca", "file4safe.com",
                       "fileband.com", "filedwon.com", "fileparadox.in", "filevice.com",
                       "hostingbulk.com", "junkyvideo.com", "linestorage.com", "ravishare.com",
                       "ryushare.com", "salefiles.com", "sendmyway.com", "sharebeast.com",
                       "sharesix.com", "thefile.me", "verzend.be", "worldbytez.com", "xvidstage.com",
                       #: NOT TESTED:
                       "101shared.com", "4upfiles.com", "filemaze.ws", "filenuke.com",
                       "linkzhost.com", "mightyupload.com", "rockdizfile.com", "sharerepo.com",
                       "shareswift.com", "uploadbaz.com", "uploadc.com", "vidbull.com",
                       "zalaa.com", "zomgupload.com",
                       #: NOT WORKING:
                       "amonshare.com", "banicrazy.info", "boosterking.com", "host4desi.com", "laoupload.com", "rd-fs.com"]
    CRYPTER_BUILTIN = ["junocloud.me", "rapidfileshare.net"]


    # def plugin_config_changed(self, plugin, name, value):
        # self.load_pattern()


    # def init(self):
        # self.event_map = {'pluginConfigChanged': "plugin_config_changed"}


    def activate(self):
        self.load_pattern()


    def load_pattern(self):
        use_builtin_list = self.get_config('use_builtin_list')

        for type, plugin in (("hoster",  "XFileSharingPro"),
                             ("crypter", "XFileSharingProFolder")):
            every_plugin = not self.get_config("use_%s_list" % type)

            if every_plugin:
                self.log_info(_("Handling any %s I can!") % type)
                pattern = self.regexp[type][0]
            else:
                plugins    = self.get_config('%s_list' % type)
                plugin_set = set(plugins.replace(' ', '').replace('\\', '').replace('|', ',').replace(';', ',').lower().split(','))

                if use_builtin_list:
                    plugin_set |= set(x.lower() for x in getattr(self, "%s_BUILTIN" % type.upper()))

                plugin_set -= set(('', u''))

                if not plugin_set:
                    self.log_info(_("No %s to handle") % type)
                    self._unload(type, plugin)
                    return

                match_list = '|'.join(sorted(plugin_set))

                len_match_list = len(plugin_set)
                self.log_info(_("Handling %d %s%s: %s") % (len_match_list,
                                                          type,
                                                          "" if len_match_list == 1 else "s",
                                                          match_list.replace('|', ', ')))

                pattern = self.regexp[type][1] % match_list.replace('.', '\.')

            dict = self.pyload.pluginManager.plugins[type][plugin]
            dict['pattern'] = pattern
            dict['re'] = re.compile(pattern)

            self.log_debug("Loaded %s pattern: %s" % (type, pattern))


    def _unload(self, type, plugin):
        dict = self.pyload.pluginManager.plugins[type][plugin]
        dict['pattern'] = r'^unmatchable$'
        dict['re'] = re.compile(dict['pattern'])


    def deactivate(self):
        # self.unload_hoster("BasePlugin")
        for type, plugin in (("hoster",  "XFileSharingPro"),
                             ("crypter", "XFileSharingProFolder")):
            self._unload(type, plugin)


    def unload_hoster(self, hoster):
        hdict = self.pyload.pluginManager.hosterPlugins[hoster]
        if "new_name" in hdict and hdict['new_name'] == "XFileSharingPro":
            if "module" in hdict:
                hdict.pop('module', None)

            if "new_module" in hdict:
                hdict.pop('new_module', None)
                hdict.pop('new_name', None)

            return True
        else:
            return False


    # def download_failed(self, pyfile):
        # if pyfile.pluginname == "BasePlugin" \
           # and pyfile.hasStatus("failed") \
           # and not self.get_config('use_hoster_list') \
           # and self.unload_hoster("BasePlugin"):
            # self.log_debug("Unloaded XFileSharingPro from BasePlugin")
            # pyfile.setStatus("queued")
