# -*- coding: utf-8 -*-

import re
import time

from .Account import Account
from .misc import decode, remove_chars, uniqify


class MultiAccount(Account):
    __name__ = "MultiAccount"
    __type__ = "account"
    __version__ = "0.22"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", True),
                  ("mh_mode", "all;listed;unlisted", "Hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Multi-hoster account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

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
        self.need_reactivate = False

        self.plugins = []
        self.supported = []

        self.pluginclass = None
        self.pluginmodule = None
        self.plugintype = None

        self.fail_count = 0

        self.init_plugin()

    def init_plugin(self):
        plugin, self.plugintype = self.pyload.pluginManager.findPlugin(self.classname)

        if plugin:
            self.pluginmodule = self.pyload.pluginManager.loadModule(self.plugintype, self.classname)
            self.pluginclass = self.pyload.pluginManager.loadClass(self.plugintype, self.classname)

            self.pyload.hookManager.addEvent("plugin_updated", self.plugins_updated)

            interval = self.config.get('mh_interval', 12) * 60 * 60
            self.periodical.start(interval, threaded=True, delay=2)

        else:
            self.log_warning(_("Multi-hoster feature will be deactivated due missing plugin reference"))

    def plugins_updated(self, type_plugins):
        if not any([t in ("internal", "hook") for t,n in type_plugins]):  #: do nothing if restart required
            self.reactivate()

    def periodical_task(self):
        self.reactivate(refresh=True)

    def replace_domains(self, list):
        for r in self.DOMAIN_REPLACEMENTS:
            pattern, repl = r
            _re = re.compile(pattern, re.I | re.U)
            list = [_re.sub(repl, domain) if _re.match(domain) else domain
                    for domain in list]

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
            hosterlist = self.grab_hosters(self.user,
                                           self.info['login']['password'],
                                           self.info['data'])

            if hosterlist and isinstance(hosterlist, list):
                domains = self.parse_domains(hosterlist)
                self.info['data']['hosters'] = sorted(domains)
                self.sync(reverse=True)

        except Exception, e:
            self.log_warning(_("Error loading hoster list for user `%s`") % self.user, e, trace=True)

        finally:
            self.log_debug("Hoster list for user `%s`: %s" % (self.user, self.info['data']['hosters']))
            return self.info['data']['hosters']

    def grab_hosters(self, user, password, data):
        """
        Load list of supported hoster
        :return: List of domain names
        """
        raise NotImplementedError

    def _override(self):
        prev_supported = self.supported
        new_supported = []
        excluded = []
        self.supported = []

        if self.plugintype == "hoster":
            plugin_map = dict((name.lower(), name)
                              for name in self.pyload.pluginManager.hosterPlugins.keys())

            account_list = [account.type.lower()
                            for account in self.pyload.api.getAccounts(False)
                            if account.valid and account.premium]

        else:
            plugin_map = {}
            account_list = [name[::-1].replace("Folder"[::-1], "", 1).lower()[::-1]
                            for name in self.pyload.pluginManager.crypterPlugins.keys()]

        for plugin in self.get_plugins():
            name = remove_chars(plugin, "-.")

            if name in account_list:
                excluded.append(plugin)

            else:
                if name in plugin_map:
                    self.supported.append(plugin_map[name])

                else:
                    new_supported.append(plugin)

        removed = [plugin for plugin in prev_supported if plugin not in self.supported]
        if removed:
            self.log_debug("Unload: %s" % ", ".join(removed))
            for plugin in removed:
                self.unload_plugin(plugin)

        if not self.supported and not new_supported:
            self.log_error(_("No %s loaded") % self.plugintype)
            return

        #: Inject plugin plugin
        self.log_debug("Overwritten %ss: %s" % (self.plugintype, ", ".join(sorted(self.supported))))

        for plugin in self.supported:
            hdict = self.pyload.pluginManager.plugins[self.plugintype][plugin]
            hdict['new_module'] = self.pluginmodule
            hdict['new_name'] = self.classname

        if excluded:
            self.log_info(_("%ss not overwritten: %s") % (self.plugintype.capitalize(), ", ".join(sorted(excluded))))

        if new_supported:
            plugins = sorted(new_supported)

            self.log_debug("New %ss: %s" % (self.plugintype, ", ".join(plugins)))

            #: Create new regexp
            pattern = r'.*(?P<DOMAIN>%s).*' % "|".join(x.replace('.', '\.')
                                                       for x in plugins)

            if hasattr(self.pluginclass, "__pattern__") and \
                    isinstance(self.pluginclass.__pattern__, basestring) and \
                            "://" in self.pluginclass.__pattern__:
                pattern = r'%s|%s' % (self.pluginclass.__pattern__, pattern)

            self.log_debug("Pattern: %s" % pattern)

            hdict = self.pyload.pluginManager.plugins[self.plugintype][self.classname]
            hdict['pattern'] = pattern
            hdict['re'] = re.compile(pattern)

    def get_plugins(self, cached=True):
        if cached and self.plugins:
            return self.plugins

        for _i in range(5):
            try:
                plugin_set = set(self._grab_hosters())
                break

            except Exception, e:
                self.log_warning(e, _("Waiting 1 minute and retry"), trace=True)
                time.sleep(60)

        else:
            self.log_warning(_("No hoster list retrieved"))
            return []

        try:
            mh_mode = self.config.get('mh_mode', 'all')
            if mh_mode in ("listed", "unlisted"):
                mh_list = self.config.get('mh_list', '').replace('|', ',').replace(';', ',').split(',')
                config_set = set(mh_list)

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


    def reactivate(self, refresh=False):
        reloading = self.info['data'].get('hosters') is not None

        if not self.info['login']['valid']:
            self.fail_count += 1
            if self.fail_count < 3:
                if reloading:
                    self.log_error(_("Could not reload hoster list - invalid account, retry in 5 minutes"))

                else:
                    self.log_error(_("Could not load hoster list - invalid account, retry in 5 minutes"))

                self.periodical.set_interval(5 * 60)

            else:
                if reloading:
                    self.log_error(_("Could not reload hoster list - invalid account, deactivating"))

                else:
                    self.log_error(_("Could not load hoster list - invalid account, deactivating"))

                self.deactivate()

            return

        if not self.logged:
            if not self.relogin():
                self.fail_count += 1
                if self.fail_count < 3:
                    if reloading:
                        self.log_error(_("Could not reload hoster list - login failed, retry in 5 minutes"))

                    else:
                        self.log_error(_("Could not load hoster list - login failed, retry in 5 minutes"))

                    self.periodical.set_interval(5 * 60)

                else:
                    if reloading:
                        self.log_error(_("Could not reload hoster list - login failed, deactivating"))

                    else:
                        self.log_error(_("Could not load hoster list - login failed, deactivating"))

                    self.deactivate()

                return

        #: Make sure we have one active hook
        try:
            self.pyload.hookManager.removeEvent("plugin_updated", self.plugins_updated)

        except ValueError:
            pass

        self.pyload.hookManager.addEvent("plugin_updated", self.plugins_updated)

        if refresh or not reloading:
            if not self.get_plugins(cached=False):
                self.fail_count += 1
                if self.fail_count < 3:
                    self.log_error(_("Failed to load hoster list for user `%s`, retry in 5 minutes") % self.user)
                    self.periodical.set_interval(5 * 60)

                else:
                    self.log_error(_("Failed to load hoster list for user `%s`, deactivating") % self.user)
                    self.deactivate()

                return

        if self.fail_count:
            self.fail_count = 0

            interval = self.config.get('mh_interval', 12) * 60 * 60
            self.periodical.set_interval(interval)

        self._override()

    def deactivate(self):
        """
        Remove override for all plugins.
        """
        self.log_info(_("Reverting back to default hosters"))

        try:
            self.pyload.hookManager.removeEvent("plugin_updated", self.plugins_updated)

        except ValueError:
            pass

        self.periodical.stop()

        self.fail_count = 0

        if self.supported:
            self.log_debug("Unload: %s" % ", ".join(self.supported))
            for plugin in self.supported:
                self.unload_plugin(plugin)

        #: Reset pattern
        hdict = self.pyload.pluginManager.plugins[self.plugintype][self.classname]

        hdict['pattern'] = getattr(self.pluginclass, "__pattern__", r'^unmatchable$')
        hdict['re'] = re.compile(hdict['pattern'])

    def updateAccounts(self, user, password=None, options={}):
        Account.updateAccounts(self, user, password, options)
        if self.need_reactivate:
            interval = self.config.get('mh_interval', 12) * 60 * 60
            self.periodical.restart(interval, threaded=True, delay=2)

        self.need_reactivate = True

    def removeAccount(self, user):
        self.deactivate()
        Account.removeAccount(self, user)
