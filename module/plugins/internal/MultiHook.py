# -*- coding: utf-8 -*-

import re
import time
import traceback

from module.plugins.internal.Hook import Hook
from module.utils import decode, remove_chars


class MultiHook(Hook):
    __name__    = "MultiHook"
    __type__    = "hook"
    __version__ = "0.54"
    __status__  = "testing"

    __config__  = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                   ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                   ("reload"        , "bool"               , "Reload plugin list"           , True ),
                   ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Hook plugin for multi hoster/crypter"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team"   , "admin@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    MIN_RELOAD_INTERVAL = 1 * 60 * 60  #: 1 hour

    DOMAIN_REPLACEMENTS = [(r'180upload\.com'  , "hundredeightyupload.com"),
                           (r'bayfiles\.net'   , "bayfiles.com"           ),
                           (r'cloudnator\.com' , "shragle.com"            ),
                           (r'dfiles\.eu'      , "depositfiles.com"       ),
                           (r'easy-share\.com' , "crocko.com"             ),
                           (r'freakshare\.net' , "freakshare.com"         ),
                           (r'hellshare\.com'  , "hellshare.cz"           ),
                           (r'ifile\.it'       , "filecloud.io"           ),
                           (r'nowdownload\.\w+', "nowdownload.sx"         ),
                           (r'nowvideo\.\w+'   , "nowvideo.sx"            ),
                           (r'putlocker\.com'  , "firedrive.com"          ),
                           (r'share-?rapid\.cz', "multishare.cz"          ),
                           (r'ul\.to'          , "uploaded.to"            ),
                           (r'uploaded\.net'   , "uploaded.to"            ),
                           (r'uploadhero\.co'  , "uploadhero.com"         ),
                           (r'zshares\.net'    , "zshare.net"             ),
                           (r'^1'              , "one"                    ),
                           (r'^2'              , "two"                    ),
                           (r'^3'              , "three"                  ),
                           (r'^4'              , "four"                   ),
                           (r'^5'              , "five"                   ),
                           (r'^6'              , "six"                    ),
                           (r'^7'              , "seven"                  ),
                           (r'^8'              , "eight"                  ),
                           (r'^9'              , "nine"                   ),
                           (r'^0'              , "zero"                   )]


    def init(self):
        self.plugins       = []
        self.supported     = []
        self.new_supported = []

        self.account      = None
        self.pluginclass  = None
        self.pluginmodule = None
        self.pluginname   = None
        self.plugintype   = None

        self.init_plugin()


    def init_plugin(self):
        self.pluginname         = self.__name__.rsplit("Hook", 1)[0]
        plugin, self.plugintype = self.pyload.pluginManager.findPlugin(self.pluginname)

        if plugin:
            self.pluginmodule = self.pyload.pluginManager.loadModule(self.plugintype, self.pluginname)
            self.pluginclass  = getattr(self.pluginmodule, self.pluginname)
        else:
            self.log_warning(_("Hook plugin will be deactivated due missing plugin reference"))
            self.set_config('activated', False)


    def load_account(self):
        self.account = self.pyload.accountManager.getAccountPlugin(self.pluginname)

        if self.account and not self.account.select()[0]:
            self.account = False

        if not self.account and hasattr(self.pluginclass, "LOGIN_ACCOUNT") and self.pluginclass.LOGIN_ACCOUNT:
            self.log_warning(_("Hook plugin will be deactivated due missing account reference"))
            self.set_config('activated', False)


    def activate(self):
        self.init_periodical(threaded=True)


    def plugins_cached(self):
        if self.plugins:
            return self.plugins

        for _i in xrange(5):
            try:
                pluginset = self._plugin_set(self.get_hosters())
                break

            except Exception, e:
                self.log_warning(e, _("Waiting 1 minute and retry"))
                time.sleep(60)
        else:
            self.log_error(_("No hoster list retrieved"))
            self.interval = self.MIN_RELOAD_INTERVAL
            return list()

        try:
            configmode = self.get_config('pluginmode', 'all')
            if configmode in ("listed", "unlisted"):
                pluginlist = self.get_config('pluginlist', '').replace('|', ',').replace(';', ',').split(',')
                configset  = self._plugin_set(pluginlist)

                if configmode == "listed":
                    pluginset &= configset
                else:
                    pluginset -= configset

        except Exception, e:
            self.log_error(e)

        self.plugins = list(pluginset)

        return self.plugins


    def _plugin_set(self, plugins):
        regexp  = re.compile(r'^[\w\-.^_]{3,63}\.[a-zA-Z]{2,}$', re.U)
        plugins = [decode(p.strip()).lower() for p in plugins if regexp.match(p.strip())]

        for r in self.DOMAIN_REPLACEMENTS:
            rf, rt  = r
            repr    = re.compile(rf, re.I|re.U)
            plugins = [re.sub(rf, rt, p) if repr.match(p) else p for p in plugins]

        return set(plugins)


    def get_hosters(self):
        """
        Load list of supported hoster

        :return: List of domain names
        """
        raise NotImplementedError


    def periodical(self):
        """
        Reload plugin list periodically
        """
        self.load_account()

        if self.get_config('reload', True):
            self.interval = max(self.get_config('reloadinterval', 12) * 60 * 60, self.MIN_RELOAD_INTERVAL)
        else:
            self.pyload.scheduler.removeJob(self.cb)
            self.cb = None

        self.log_info(_("Reloading supported %s list") % self.plugintype)

        old_supported = self.supported

        self.supported     = []
        self.new_supported = []
        self.plugins       = []

        self.override_plugins()

        old_supported = [plugin for plugin in old_supported if plugin not in self.supported]

        if old_supported:
            self.log_debug("Unload: %s" % ", ".join(old_supported))
            for plugin in old_supported:
                self.unload_plugin(plugin)


    def override_plugins(self):
        excludedList = []

        if self.plugintype == "hoster":
            pluginMap    = dict((name.lower(), name) for name in self.pyload.pluginManager.hosterPlugins.keys())
            accountList  = [account.type.lower() for account in self.pyload.api.getAccounts(False) if account.valid and account.premium]
        else:
            pluginMap    = {}
            accountList  = [name[::-1].replace("Folder"[::-1], "", 1).lower()[::-1] for name in self.pyload.pluginManager.crypterPlugins.keys()]

        for plugin in self.plugins_cached():
            name = remove_chars(plugin, "-.")

            if name in accountList:
                excludedList.append(plugin)
            else:
                if name in pluginMap:
                    self.supported.append(pluginMap[name])
                else:
                    self.new_supported.append(plugin)

        if not self.supported and not self.new_supported:
            self.log_error(_("No %s loaded") % self.plugintype)
            return

        #: Inject plugin plugin
        self.log_debug("Overwritten %ss: %s" % (self.plugintype, ", ".join(sorted(self.supported))))

        for plugin in self.supported:
            hdict = self.pyload.pluginManager.plugins[self.plugintype][plugin]
            hdict['new_module'] = self.pluginmodule
            hdict['new_name']   = self.pluginname

        if excludedList:
            self.log_info(_("%ss not overwritten: %s") % (self.plugintype.capitalize(), ", ".join(sorted(excludedList))))

        if self.new_supported:
            plugins = sorted(self.new_supported)

            self.log_debug("New %ss: %s" % (self.plugintype, ", ".join(plugins)))

            #: Create new regexp
            regexp = r'.*(?P<DOMAIN>%s).*' % "|".join(x.replace('.', '\.') for x in plugins)
            if hasattr(self.pluginclass, "__pattern__") and isinstance(self.pluginclass.__pattern__, basestring) and "://" in self.pluginclass.__pattern__:
                regexp = r'%s|%s' % (self.pluginclass.__pattern__, regexp)

            self.log_debug("Regexp: %s" % regexp)

            hdict = self.pyload.pluginManager.plugins[self.plugintype][self.pluginname]
            hdict['pattern'] = regexp
            hdict['re']      = re.compile(regexp)


    def unload_plugin(self, plugin):
        hdict = self.pyload.pluginManager.plugins[self.plugintype][plugin]
        if "module" in hdict:
            hdict.pop('module', None)

        if "new_module" in hdict:
            hdict.pop('new_module', None)
            hdict.pop('new_name', None)


    def deactivate(self):
        """
        Remove override for all plugins. Scheduler job is removed by hookmanager
        """
        for plugin in self.supported:
            self.unload_plugin(plugin)

        #: Reset pattern
        hdict = self.pyload.pluginManager.plugins[self.plugintype][self.pluginname]

        hdict['pattern'] = getattr(self.pluginclass, "__pattern__", r'^unmatchable$')
        hdict['re']      = re.compile(hdict['pattern'])
