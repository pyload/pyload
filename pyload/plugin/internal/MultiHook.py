# -*- coding: utf-8 -*-

import re

from time import sleep

from pyload.plugin.Hook import Hook
from pyload.utils import decode, remove_chars


class MultiHook(Hook):
    __name    = "MultiHook"
    __type    = "hook"
    __version = "0.37"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Hook plugin for multi hoster/crypter"""
    __license     = "GPLv3"
    __authors     = [("pyLoad Team", "admin@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    MIN_INTERVAL = 1 * 60 * 60

    DOMAIN_REPLACEMENTS = [(r'180upload\.com'  , "hundredeightyupload.com"),
                           (r'1fichier\.com'   , "onefichier.com"         ),
                           (r'2shared\.com'    , "twoshared.com"          ),
                           (r'4shared\.com'    , "fourshared.com"         ),
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
                           (r'(\d+.+)'         , "X\1"                    )]


    def setup(self):
        self.plugins       = []
        self.supported     = []
        self.new_supported = []

        self.account      = None
        self.pluginclass  = None
        self.pluginmodule = None
        self.pluginname   = None
        self.plugintype   = None

        self._initPlugin()


    def _initPlugin(self):
        plugin, type = self.core.pluginManager.findPlugin(self.__name)

        if not plugin:
            self.logWarning("Hook plugin will be deactivated due missing plugin reference")
            self.setConfig('activated', False)
        else:
            self.pluginname   = self.__name
            self.plugintype   = type
            self.pluginmodule = self.core.pluginManager.loadModule(type, self.__name)
            self.pluginclass  = getattr(self.pluginmodule, self.__name)


    def _loadAccount(self):
        self.account = self.core.accountManager.getAccountPlugin(self.pluginname)

        if self.account and not self.account.canUse():
            self.account = None

        if not self.account and hasattr(self.pluginclass, "LOGIN_ACCOUNT") and self.pluginclass.LOGIN_ACCOUNT:
            self.logWarning("Hook plugin will be deactivated due missing account reference")
            self.setConfig('activated', False)


    def activate(self):
        self._loadAccount()


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


    def getConfig(self, option, default=''):
        """getConfig with default value - sublass may not implements all config options"""
        try:
            return self.getConf(option)

        except KeyError:
            return default


    def pluginsCached(self):
        if self.plugins:
            return self.plugins

        for _i in xrange(3):
            try:
                pluginset = self._pluginSet(self.getHosters() if self.plugintype == "hoster" else self.getCrypters())

            except Exception, e:
                self.logError(e, "Waiting 1 minute and retry")
                sleep(60)

            else:
                break
        else:
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
        plugins = set((decode(x).strip().lower() for x in plugins if '.' in x))

        for rf, rt in self.DOMAIN_REPLACEMENTS:
            regex = re.compile(rf)
            for p in filter(lambda x: regex.match(x), plugins):
                plugins.remove(p)
                plugins.add(re.sub(rf, rt, p))

        plugins.discard('')

        return plugins


    def getHosters(self):
        """Load list of supported hoster

        :return: List of domain names
        """
        raise NotImplementedError


    def getCrypters(self):
        """Load list of supported crypters

        :return: List of domain names
        """
        raise NotImplementedError


    def periodical(self):
        """reload plugin list periodically"""
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

        if self.getConfig("reload", True):
            self.interval = max(self.getConfig("reloadinterval", 12) * 60 * 60, self.MIN_INTERVAL)
        else:
            self.core.scheduler.removeJob(self.cb)
            self.cb = None


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
            regexp = r'.*(?P<DOMAIN>%s).*' % "|".join([x.replace(".", "\.") for x in plugins])
            if hasattr(self.pluginclass, "__pattern") and isinstance(self.pluginclass.__pattern, basestring) and '://' in self.pluginclass.__pattern:
                regexp = r'%s|%s' % (self.pluginclass.__pattern, regexp)

            self.logDebug("Regexp: %s" % regexp)

            hdict = self.core.pluginManager.plugins[self.plugintype][self.pluginname]
            hdict['pattern'] = regexp
            hdict['re']      = re.compile(regexp)


    def unloadPlugin(self, plugin):
        hdict = self.core.pluginManager.plugins[self.plugintype][plugin]
        if "module" in hdict:
            del hdict['module']

        if "new_module" in hdict:
            del hdict['new_module']
            del hdict['new_name']


    def deactivate(self):
        """Remove override for all plugins. Scheduler job is removed by hookmanager"""
        for plugin in self.supported:
            self.unloadPlugin(plugin)

        # reset pattern
        hdict = self.core.pluginManager.plugins[self.plugintype][self.pluginname]

        hdict['pattern'] = getattr(self.pluginclass, "__pattern", r'^unmatchable$')
        hdict['re']      = re.compile(hdict['pattern'])


    def downloadFailed(self, pyfile):
        """remove plugin override if download fails but not if file is offline/temp.offline"""
        if pyfile.status != 8 or not self.getConfig("revertfailed", True):
            return

        hdict = self.core.pluginManager.plugins[self.plugintype][pyfile.pluginname]
        if "new_name" in hdict and hdict['new_name'] == self.pluginname:
            if pyfile.error == "MultiHook":
                self.logDebug("Unload MultiHook", pyfile.pluginname, hdict)
                self.unloadPlugin(pyfile.pluginname)
                pyfile.setStatus("queued")
                pyfile.sync()
            else:
                retries   = max(self.getConfig("retry", 10), 0)
                wait_time = max(self.getConfig("retryinterval", 1), 0)

                if 0 < retries > pyfile.plugin.retries:
                    self.logInfo(_("Retrying: %s") % pyfile.name)
                    pyfile.setCustomStatus("MultiHook", "queued")
                    pyfile.sync()

                    pyfile.plugin.retries += 1
                    pyfile.plugin.setWait(wait_time)
                    pyfile.plugin.wait()
