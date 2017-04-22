# -*- coding: utf-8 -*-

import inspect
import re

from ..internal.Addon import Addon


class XFileSharing(Addon):
    __name__ = "XFileSharing"
    __type__ = "hook"
    __version__ = "0.56"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("use_hoster_list", "bool", "Load listed hosters only", False),
                  ("use_crypter_list", "bool", "Load listed crypters only", False),
                  ("use_builtin_list", "bool", "Load built-in plugin list", True),
                  ("hoster_list", "str", "Hoster list (comma separated)", ""),
                  ("crypter_list", "str", "Crypter list (comma separated)", "")]

    __description__ = """Load XFileSharing hosters and crypters which don't need a own plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    _regexmap = {'hoster': (r'(?:https?://(?:www\.)?)(?!(?:www\.)?(?:%s))(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,63}(?:\.[a-zA-Z]{2,})+)(?:\:\d+)?)/(?:embed-)?\w{12}(?:\W|$)',
                            r'https?://(?:[^/]+\.)?(?P<DOMAIN>%s)/(?:embed-)?\w+'),
                 'crypter': (r'(?:https?://(?:www\.)?)(?!(?:www\.)?(?:%s))(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,63}(?:\.[a-zA-Z]{2,})+)(?:\:\d+)?)/(?:user|folder)s?/\w+',
                             r'https?://(?:[^/]+\.)?(?P<DOMAIN>%s)/(?:user|folder)s?/\w+')}

    BUILTIN_HOSTERS = [  # WORKING HOSTERS:
        "ani-stream.com", "backin.net", "cloudshares.net", "cloudsix.me",
        "eyesfile.ca", "file4safe.com", "fileband.com", "filedwon.com",
        "fileparadox.in", "filevice.com", "hostingbulk.com", "junkyvideo.com",
        "ravishare.com", "salefiles.com", "sendmyway.com", "sharebeast.com",
        "sharesix.com", "thefile.me", "verzend.be", "worldbytez.com",
                        "xvidstage.com",
                        # NOT TESTED:
                        "101shared.com", "4upfiles.com", "filemaze.ws", "filenuke.com",
                        "linkzhost.com", "mightyupload.com", "rockdizfile.com", "sharerepo.com",
                        "shareswift.com", "uploadbaz.com", "uploadc.com", "vidbull.com",
                        "zalaa.com", "zomgupload.com",
                        # NOT WORKING:
                        "amonshare.com", "banicrazy.info", "boosterking.com", "host4desi.com",
                        "laoupload.com", "rd-fs.com"]
    BUILTIN_CRYPTERS = ["junocloud.me", "rapidfileshare.net"]

    def activate(self):
        for type, plugin in (("hoster", "XFileSharing"),
                             ("crypter", "XFileSharingFolder")):
            self._load(type, plugin)

    def deactivate(self):
        for type, plugin in (("hoster", "XFileSharing"),
                             ("crypter", "XFileSharingFolder")):
            self._unload(type, plugin)

    def get_pattern(self, type, plugin):
        if self.config.get('use_%s_list' % type):
            plugin_list = self.config.get('%s_list' % type)
            plugin_list = plugin_list.replace(' ', '').replace('\\', '')
            plugin_list = plugin_list.replace('|', ',').replace(';', ',')
            plugin_list = plugin_list.lower().split(',')

            plugin_set = set(plugin_list)

            if self.config.get('use_builtin_list'):
                builtin_list = getattr(self, "BUILTIN_%sS" % type.upper())
                plugin_set.update(builtin_list)

            plugin_set.difference_update(('', u''))

            if not plugin_set:
                self.log_info(_("No %s to handle") % type)
                return

            match_list = '|'.join(sorted(plugin_set)).replace('.', '\.')
            pattern = self._regexmap[type][1] % match_list

            self.log_info(_("Handle %d %s%s: %s") %
                          (len(plugin_set),
                           type,
                           "" if len(plugin_set) == 1 else "s",
                           match_list.replace('\.', '.').replace('|', ', ')))
        else:
            plugin_list = []
            isXFS = lambda klass: any(k.__name__.startswith("XFS")
                                      for k in inspect.getmro(klass))

            for p in self.pyload.pluginManager.plugins[type].values():
                try:
                    klass = self.pyload.pluginManager.loadClass(type, p[
                                                                'name'])

                except AttributeError, e:
                    self.log_debug(e, trace=True)
                    continue

                if hasattr(klass, "PLUGIN_DOMAIN") and klass.PLUGIN_DOMAIN and isXFS(
                        klass):
                    plugin_list.append(klass.PLUGIN_DOMAIN)

            if plugin_list:
                unmatch_list = '|'.join(sorted(plugin_list)).replace('.', '\.')
                pattern = self._regexmap[type][0] % unmatch_list
            else:
                pattern = self._regexmap[type][0]

            self.log_info(_("Auto-discover new %ss") % type)

        return pattern

    def _load(self, type, plugin):
        dict = self.pyload.pluginManager.plugins[type][plugin]
        pattern = self.get_pattern(type, plugin)

        if not pattern:
            return

        dict['pattern'] = pattern
        dict['re'] = re.compile(pattern)

        self.log_debug("Pattern for %ss: %s" % (type, pattern))

    def _unload(self, type, plugin):
        dict = self.pyload.pluginManager.plugins[type][plugin]
        dict['pattern'] = r'^unmatchable$'
        dict['re'] = re.compile(dict['pattern'])
