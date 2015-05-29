# -*- coding: utf-8 -*-

import re
import time
import traceback

from module.plugins.Hook import Hook
from module.utils import decode, remove_chars


class MultiHook(Hook):
    __name__    = "MultiHook"
    __type__    = "hook"
    __version__ = "0.45"

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


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10

        self.plugins       = []
        self.supported     = []
        self.new_supported = []

        self.account      = None
        self.pluginclass  = None
        self.pluginmodule = None
        self.pluginname   = None
        self.plugintype   = None

        self.initPlugin()


    def initPlugin(self):
        self.pluginname         = self.__name__.rsplit("Hook", 1)[0]
        plugin, self.plugintype = self.core.pluginManager.findPlugin(self.pluginname)

        if plugin:
            self.pluginmodule = self.core.pluginManager.loadModule(self.plugintype, self.pluginname)
            self.pluginclass  = getattr(self.pluginmodule, self.pluginname)
        else:
            self.logWarning("Hook plugin will be deactivated due missing plugin reference")
            self.setConfig('activated', False)


    def loadAccount(self):
        self.account = self.core.accountManager.getAccountPlugin(self.pluginname)

        if self.account and not self.account.canUse():
            self.account = None

        if not self.account and hasattr(self.pluginclass, "LOGIN_ACCOUNT") and self.pluginclass.LOGIN_ACCOUNT:
            self.logWarning("Hook plugin will be deactivated due missing account reference")
            self.setConfig('activated', False)


    def getURL(self, *args, **kwargs):  #@TODO: Remove in 0.4.10
        """ see HTTPRequest for argument list """
        h = pyreq.getHTTPRequest(timeout=120)
        try:
            if not 'decode' in kwargs:
                kwargs['decode'] = True
            rep = h.load(*args, **kwargs)
        finally:
            h.close()

        return rep


    def getConfig(self, option, default=''):  #@TODO: Remove in 0.4.10
        """getConfig with default value - sublass may not implements all config options"""
        try:
            return self.getConf(option)

        except KeyError:
            return default


    def pluginsCached(self):
        if self.plugins:
            return self.plugins

        for _i in xrange(2):
            try:
                pluginset = self._pluginSet(self.getHosters())
                break

            except Exception, e:
                self.logDebug(e, "Waiting 1 minute and retry")
                time.sleep(60)
        else:
            self.logWarning(_("Fallback to default reload interval due plugin parse error"))
            self.interval = self.MIN_RELOAD_INTERVAL
            return list()

        try:
            configmode = self.getConfig("pluginmode", 'all')
            if configmode in ("listed", "unlisted"):
                pluginlist = self.getConfig("pluginlist", '').replace('|', ',').replace(';', ',').split(',')
                configset  = self._pluginSet(pluginlist)

                if configmode == "listed":
                    pluginset &= configset
                else:
                    pluginset -= configset

        except Exception, e:
            self.logError(e)

        self.plugins = list(pluginset)

        return self.plugins


    def _pluginSet(self, plugins):
        regexp  = re.compile(r'^[\w\-.^_]{3,63}\.[a-zA-Z]{2,}$', re.U)
        plugins = [decode(p.strip()).lower() for p in plugins if regexp.match(p.strip())]

        for r in self.DOMAIN_REPLACEMENTS:
            rf, rt  = r
            repr    = re.compile(rf, re.I|re.U)
            plugins = [re.sub(rf, rt, p) if repr.match(p) else p for p in plugins]

        return set(plugins)


    def getHosters(self):
        """Load list of supported hoster

        :return: List of domain names
        """
        raise NotImplementedError


    #: Threaded _periodical, remove in 0.4.10 and use built-in flag for that
    def _periodical(self):
        try:
            if self.isActivated():
                self.periodical()

        except Exception, e:
            self.core.log.error(_("Error executing hooks: %s") % str(e))
            if self.core.debug:
                traceback.print_exc()

        self.cb = self.core.scheduler.addJob(self.interval, self._periodical)


    def periodical(self):
        """reload plugin list periodically"""
        self.loadAccount()

        if self.getConfig("reload", True):
            self.interval = max(self.getConfig("reloadinterval", 12) * 60 * 60, self.MIN_RELOAD_INTERVAL)
        else:
            self.core.scheduler.removeJob(self.cb)
            self.cb = None

        self.logInfo(_("Reloading supported %s list") % self.plugintype)

        old_supported = self.supported

        self.supported     = []
        self.new_supported = []
        self.plugins       = []

        self.overridePlugins()

        old_supported = [plugin for plugin in old_supported if plugin not in self.supported]

        if old_supported:
            self.logDebug("Unload: %s" % ", ".join(old_supported))
            for plugin in old_supported:
                self.unloadPlugin(plugin)


    def overridePlugins(self):
        excludedList = []

        if self.plugintype == "hoster":
            pluginMap    = dict((name.lower(), name) for name in self.core.pluginManager.hosterPlugins.iterkeys())
            accountList  = [account.type.lower() for account in self.core.api.getAccounts(False) if account.valid and account.premium]
        else:
            pluginMap    = {}
            accountList  = [name[::-1].replace("Folder"[::-1], "", 1).lower()[::-1] for name in self.core.pluginManager.crypterPlugins.iterkeys()]

        for plugin in self.pluginsCached():
            name = remove_chars(plugin, "-.")

            if name in accountList:
                excludedList.append(plugin)
            else:
                if name in pluginMap:
                    self.supported.append(pluginMap[name])
                else:
                    self.new_supported.append(plugin)

        if not self.supported and not self.new_supported:
            self.logError(_("No %s loaded") % self.plugintype)
            return

        # inject plugin plugin
        self.logDebug("Overwritten %ss: %s" % (self.plugintype, ", ".join(sorted(self.supported))))

        for plugin in self.supported:
            hdict = self.core.pluginManager.plugins[self.plugintype][plugin]
            hdict['new_module'] = self.pluginmodule
            hdict['new_name']   = self.pluginname

        if excludedList:
            self.logInfo(_("%ss not overwritten: %s") % (self.plugintype.capitalize(), ", ".join(sorted(excludedList))))

        if self.new_supported:
            plugins = sorted(self.new_supported)

            self.logDebug("New %ss: %s" % (self.plugintype, ", ".join(plugins)))

            # create new regexp
            regexp = r'.*(?P<DOMAIN>%s).*' % "|".join(x.replace('.', '\.') for x in plugins)
            if hasattr(self.pluginclass, "__pattern__") and isinstance(self.pluginclass.__pattern__, basestring) and '://' in self.pluginclass.__pattern__:
                regexp = r'%s|%s' % (self.pluginclass.__pattern__, regexp)

            self.logDebug("Regexp: %s" % regexp)

            hdict = self.core.pluginManager.plugins[self.plugintype][self.pluginname]
            hdict['pattern'] = regexp
            hdict['re']      = re.compile(regexp)


    def unloadPlugin(self, plugin):
        hdict = self.core.pluginManager.plugins[self.plugintype][plugin]
        if "module" in hdict:
            hdict.pop('module', None)

        if "new_module" in hdict:
            hdict.pop('new_module', None)
            hdict.pop('new_name', None)


    def unload(self):
        """Remove override for all plugins. Scheduler job is removed by hookmanager"""
        for plugin in self.supported:
            self.unloadPlugin(plugin)

        # reset pattern
        hdict = self.core.pluginManager.plugins[self.plugintype][self.pluginname]

        hdict['pattern'] = getattr(self.pluginclass, "__pattern__", r'^unmatchable$')
        hdict['re']      = re.compile(hdict['pattern'])
