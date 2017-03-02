# -*- coding: utf-8 -*-

import re
import time

from .Account import Account
from .misc import decode, remove_chars, uniqify


class MultiAccount(Account):
    __name__ = "MultiAccount"
    __type__ = "account"
    __version__ = "0.14"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", True),
                  ("mh_mode", "all;listed;unlisted", "Hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Multi-hoster account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PERIODICAL_INTERVAL = 1  #: 1 hour

    DOMAIN_REPLACEMENTS = [(r'180upload\.com', "hundredeightyupload.com"),
                           (r'bayfiles\.net', "bayfiles.com"),
                           (r'cloudnator\.com', "shragle.com"),
                           (r'dfiles\.eu', "depositfiles.com"),
                           (r'easy-share\.com', "crocko.com"),
                           (r'freakshare\.net', "freakshare.com"),
                           (r'hellshare\.com', "hellshare.cz"),
                           (r'ifile\.it', "filecloud.io"),
                           (r'nowdownload\.\w+', "nowdownload.sx"),
                           (r'nowvideo\.\w+', "nowvideo.sx"),
                           (r'putlocker\.com', "firedrive.com"),
                           (r'share-?rapid\.cz', "multishare.cz"),
                           (r'ul\.to', "uploaded.to"),
                           (r'uploaded\.net', "uploaded.to"),
                           (r'uploadhero\.co', "uploadhero.com"),
                           (r'zshares\.net', "zshare.net"),
                           (r'^1', "one"),
                           (r'^2', "two"),
                           (r'^3', "three"),
                           (r'^4', "four"),
                           (r'^5', "five"),
                           (r'^6', "six"),
                           (r'^7', "seven"),
                           (r'^8', "eight"),
                           (r'^9', "nine"),
                           (r'^0', "zero")]

    def init(self):
        self.plugins = []
        self.supported = []

        self.pluginclass = None
        self.pluginmodule = None
        self.plugintype = None

        self.pyload.hookManager.addEvent(
            "plugin_updated", self.plugins_updated)

        self.init_plugin()

    def init_plugin(self):
        plugin, self.plugintype = self.pyload.pluginManager.findPlugin(
            self.classname)

        if plugin:
            self.pluginmodule = self.pyload.pluginManager.loadModule(
                self.plugintype, self.classname)
            self.pluginclass = self.pyload.pluginManager.loadClass(
                self.plugintype, self.classname)

            interval = self.config.get('mh_interval', 12) * 60 * 60
            self.periodical.start(interval, threaded=True, delay=2)

        else:
            self.log_warning(
                _("Multi-hoster feature will be deactivated due missing plugin reference"))

    def plugins_updated(self, type_plugins):
        if not self.info['login']['valid']:
            self.log_error(_("Could not %s hoster list - invalid account, retry in 5 minutes") %
                           ("reload" if self.info['data'].get('hosters') else "load"))
            self.periodical.set_interval(5 * 60)
            return

        if not self.logged:
            if not self.relogin():
                self.log_error(_("Could not %s hoster list - login failed, retry in 5 minutes") %
                               ("reload" if self.info['data'].get('hosters') else "load"))
                self.periodical.set_interval(5 * 60)
                return

        self._override()

    def replace_domains(self, list):
        for r in self.DOMAIN_REPLACEMENTS:
            pattern, repl = r
            _re = re.compile(pattern, re.I | re.U)
            list = [_re.sub(repl, domain) if _re.match(
                domain) else domain for domain in list]

        return list

    def parse_domains(self, list):
        _re = re.compile(r'^(?:https?://)?(?:www\.)?(?:\w+\.)*((?:(?:\d{1,3}\.){3}\d{1,3}|[\w\-^_]{3,63}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)',
                         re.I | re.U)

        domains = [decode(domain).strip().lower()
                   for url in list for domain in _re.findall(url)]
        return self.replace_domains(uniqify(domains))

    def _grab_hosters(self):
        self.info['data']['hosters'] = []
        try:
            hosterlist = self.grab_hosters(self.user, self.info['login'][
                                           'password'], self.info['data'])

            if hosterlist and isinstance(hosterlist, list):
                domains = self.parse_domains(hosterlist)
                self.info['data']['hosters'] = sorted(domains)

        except Exception, e:
            self.log_warning(
                _("Error loading hoster list for user `%s`") %
                self.user, e, trace=True)

        finally:
            return self.info['data']['hosters']

    def grab_hosters(self, user, password, data):
        """
        Load list of supported hoster
        :return: List of domain names
        """
        raise NotImplementedError

    def periodical_task(self):
        self.log_info(_("%s hoster list for user `%s`...") %
                      ("Reloading" if self.info['data'].get('hosters') else "Loading", self.user))

        if not self.info['login']['valid']:
            self.log_error(_("Could not %s hoster list - invalid account, retry in 5 minutes") %
                           ("reload" if self.info['data'].get('hosters') else "load"))
            self.periodical.set_interval(5 * 60)
            return

        if not self.logged:
            if not self.relogin():
                self.log_error(_("Could not %s hoster list - login failed, retry in 5 minutes") %
                               ("reload" if self.info['data'].get('hosters') else "load"))
                self.periodical.set_interval(5 * 60)
                return

        hosters = self._grab_hosters()
        if hosters:
            self.log_debug(
                "Hoster list for user `%s`: %s" % (self.user, hosters))

            self._override()

            self.periodical.set_interval(
                self.config.get(
                    'mh_interval',
                    12) * 60 * 60)

        else:
            self.log_error(
                _("Failed to load hoster list for user `%s`") %
                self.user)

    def _override(self):
        prev_supported = self.supported
        newsupported = []
        excluded = []
        self.supported = []
        self.plugins = []

        if self.plugintype == "hoster":
            plugin_map = dict((name.lower(), name)
                              for name in self.pyload.pluginManager.hosterPlugins.keys())
            account_list = [account.type.lower() for account in self.pyload.api.getAccounts(
                False) if account.valid and account.premium]

        else:
            plugin_map = {}
            account_list = [
                name[::-1].replace("Folder"[::-1], "", 1).lower()[::-1]
                for name in self.pyload.pluginManager.crypterPlugins.keys()
            ]

        for plugin in self.plugins_cached():
            name = remove_chars(plugin, "-.")

            if name in account_list:
                excluded.append(plugin)
            else:
                if name in plugin_map:
                    self.supported.append(plugin_map[name])
                else:
                    newsupported.append(plugin)

        removed = [
            plugin for plugin in prev_supported if plugin not in self.supported]
        if removed:
            self.log_debug("Unload: %s" % ", ".join(removed))
            for plugin in removed:
                self.unload_plugin(plugin)

        if not self.supported and not newsupported:
            self.log_error(_("No %s loaded") % self.plugintype)
            return

        #: Inject plugin plugin
        self.log_debug("Overwritten %ss: %s" %
                       (self.plugintype, ", ".join(sorted(self.supported))))

        for plugin in self.supported:
            hdict = self.pyload.pluginManager.plugins[self.plugintype][plugin]
            hdict['new_module'] = self.pluginmodule
            hdict['new_name'] = self.classname

        if excluded:
            self.log_info(
                _("%ss not overwritten: %s") %
                (self.plugintype.capitalize(), ", ".join(
                    sorted(excluded))))

        if newsupported:
            plugins = sorted(newsupported)

            self.log_debug(
                "New %ss: %s" % (self.plugintype, ", ".join(plugins)))

            #: Create new regexp
            pattern = r'.*(?P<DOMAIN>%s).*' % "|".join(x.replace('.', '\.')
                                                       for x in plugins)
            if hasattr(self.pluginclass, "__pattern__") and isinstance(
                    self.pluginclass.__pattern__, basestring) and "://" in self.pluginclass.__pattern__:
                pattern = r'%s|%s' % (self.pluginclass.__pattern__, pattern)

            self.log_debug("Pattern: %s" % pattern)

            hdict = self.pyload.pluginManager.plugins[
                self.plugintype][self.classname]
            hdict['pattern'] = pattern
            hdict['re'] = re.compile(pattern)

    def plugins_cached(self):
        if self.plugins:
            return self.plugins

        for _i in range(5):
            try:
                plugin_set = set(self._grab_hosters())
                break

            except Exception, e:
                self.log_warning(
                    e, _("Waiting 1 minute and retry"), trace=True)
                time.sleep(60)

        else:
            self.log_warning(
                _("No hoster list retrieved, will retry in %s hour(s)") %
                self.PERIODICAL_INTERVAL)
            self.periodical.set_interval(self.PERIODICAL_INTERVAL * 60 * 60)
            return []

        try:
            mh_mode = self.config.get('mh_mode', 'all')
            if mh_mode in ("listed", "unlisted"):
                plugin_list = self.config.get(
                    'plugin_list',
                    '').replace(
                    '|',
                    ',').replace(
                    ';',
                    ',').split(',')
                config_set = set(plugin_list)

                if mh_mode == "listed":
                    plugin_set &= config_set
                else:
                    plugin_set -= config_set

        except Exception, e:
            self.log_error(e)

        self.plugins = list(plugin_set)

        return self.plugins

    def unload_plugin(self, plugin):
        #: Reset module
        hdict = self.pyload.pluginManager.plugins[self.plugintype][plugin]
        if "module" in hdict:
            hdict.pop('module', None)

        if "new_module" in hdict:
            hdict.pop('new_module', None)
            hdict.pop('new_name', None)

    def deactivate(self):
        """
        Remove override for all plugins.
        """
        self.log_info(_("Reverting back to default hosters"))

        self.pyload.hookManager.removeEvent(
            "plugin_updated", self.plugins_updated)
        self.periodical.stop()

        self.log_debug("Unload: %s" % ", ".join(self.supported))
        for plugin in self.supported:
            self.unload_plugin(plugin)

        #: Reset pattern
        hdict = self.pyload.pluginManager.plugins[
            self.plugintype][self.classname]

        hdict['pattern'] = getattr(
            self.pluginclass,
            "__pattern__",
            r'^unmatchable$')
        hdict['re'] = re.compile(hdict['pattern'])

    def removeAccount(self, user):
        self.deactivate()
        super(MultiAccount, self).removeAccount(user)
