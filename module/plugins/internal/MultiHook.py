# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook
from module.utils import remove_chars


class MultiHook(Hook):
    __name__    = "MultiHook"
    __type__    = "hook"
    __version__ = "0.26"

    __config__ = [("mode"        , "all;listed;unlisted", "Use for plugins (if supported)"               , "all"),
                  ("pluginlist"  , "str"                , "Plugin list (comma separated)"                , ""   ),
                  ("revertfailed", "bool"               , "Revert to standard download if download fails", False),
                  ("interval"    , "int"                , "Reload interval in hours (0 to disable)"      , 12   )]

    __description__ = """Hook plugin for multi hoster/crypter"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    MIN_INTERVAL = 12 * 60 * 60  #: reload plugins every 12h

    PLUGIN_REPLACEMENTS = [("1fichier.com"   , "onefichier.com"),
                           ("2shared.com"    , "twoshared.com" ),
                           ("4shared.com"    , "fourshared.com"),
                           ("cloudnator.com" , "shragle.com"   ),
                           ("easy-share.com" , "crocko.com"    ),
                           ("fileparadox.com", "fileparadox.in"),
                           ("freakshare.net" , "freakshare.com"),
                           ("hellshare.com"  , "hellshare.cz"  ),
                           ("ifile.it"       , "filecloud.io"  ),
                           ("nowdownload.ch" , "nowdownload.sx"),
                           ("nowvideo.co"    , "nowvideo.sx"   ),
                           ("putlocker.com"  , "firedrive.com" ),
                           ("share-rapid.cz" , "multishare.cz" ),
                           ("sharerapid.cz"  , "multishare.cz" ),
                           ("ul.to"          , "uploaded.to"   ),
                           ("uploaded.net"   , "uploaded.to"   )]


    def setup(self):
        self.type          = self.core.pluginManager.findPlugin(self.__name__)[1] or "hoster"
        self.plugins       = []
        self.supported     = []
        self.new_supported = []


    def getURL(self, *args, **kwargs):  #@TODO: Remove in 0.4.10
        """ see HTTPRequest for argument list """
        h = pyreq.getHTTPRequest(timeout=120)
        try:
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


    def pluginCached(self):
        if not self.plugins:
            try:
                pluginset = self.pluginSet(self.getHosters() if self.type == "hoster" else self.getCrypters())
            except Exception, e:
                self.logError(e)
                return []

            try:
                configmode = self.getConfig("mode", 'all')
                if configmode in ("listed", "unlisted"):
                    pluginlist = self.getConfig("pluginlist", '').replace('|', ',').replace(';', ',').split(',')
                    configset  = self.pluginSet(pluginlist)

                    if configmode == "listed":
                        pluginset &= configset
                    else:
                        pluginset -= configset

            except Exception, e:
                self.logError(e)

            self.plugins = list(pluginset)

        return self.plugins


    def pluginSet(self, plugins):
        plugins = set((str(x).strip().lower() for x in plugins))

        for rep in self.PLUGIN_REPLACEMENTS:
            if rep[0] in plugins:
                plugins.remove(rep[0])
                plugins.add(rep[1])

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
        self.interval = max(self.getConfig("interval", 0), self.MIN_INTERVAL)

        self.logInfo(_("Reloading supported %s list") % self.type)

        old_supported      = self.supported
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

        if self.type == "hoster":
            pluginMap    = dict((name.lower(), name) for name in self.core.pluginManager.hosterPlugins.iterkeys())
            accountList  = [account.type.lower() for account in self.core.api.getAccounts(False) if account.valid and account.premium]
        else:
            pluginMap    = {}
            accountList  = [name[::-1].replace("Folder"[::-1], "", 1).lower()[::-1] for name in self.core.pluginManager.crypterPlugins.iterkeys()]

        for plugin in self.pluginCached():
            name = remove_chars(plugin, "-.")

            if name in accountList:
                excludedList.append(plugin)
            else:
                if name in pluginMap:
                    self.supported.append(pluginMap[name])
                else:
                    self.new_supported.append(plugin)

        if not self.supported and not self.new_supported:
            self.logError(_("No %s loaded") % self.type)
            return

        module = self.core.pluginManager.getPlugin(self.__name__)
        klass  = getattr(module, self.__name__)

        # inject plugin plugin
        self.logDebug("Overwritten %ss: %s" % (self.type, ", ".join(sorted(self.supported))))

        for plugin in self.supported:
            hdict = self.core.pluginManager.plugins[self.type][plugin]
            hdict['new_module'] = module
            hdict['new_name']   = self.__name__

        if excludedList:
            self.logInfo(_("%ss not overwritten: %s") % (self.type.capitalize(), ", ".join(sorted(excludedList))))

        if self.new_supported:
            plugins = sorted(self.new_supported)

            self.logDebug("New %ss: %s" % (self.type, ", ".join(plugins)))

            # create new regexp
            regexp = r'.*(%s).*' % "|".join([x.replace(".", "\.") for x in plugins])
            if hasattr(klass, "__pattern__") and isinstance(klass.__pattern__, basestring) and '://' in klass.__pattern__:
                regexp = r'%s|%s' % (klass.__pattern__, regexp)

            self.logDebug("Regexp: %s" % regexp)

            hdict = self.core.pluginManager.plugins[self.type][self.__name__]
            hdict['pattern'] = regexp
            hdict['re']      = re.compile(regexp)


    def unloadPlugin(self, plugin):
        hdict = self.core.pluginManager.plugins[self.type][plugin]
        if "module" in hdict:
            del hdict['module']

        if "new_module" in hdict:
            del hdict['new_module']
            del hdict['new_name']


    def unload(self):
        """Remove override for all plugins. Scheduler job is removed by hookmanager"""
        for plugin in self.supported:
            self.unloadPlugin(plugin)

        # reset pattern
        klass = getattr(self.core.pluginManager.getPlugin(self.__name__), self.__name__)
        hdict = self.core.pluginManager.plugins[self.type][self.__name__]

        hdict['pattern'] = getattr(klass, "__pattern__", r'^unmatchable$')
        hdict['re']      = re.compile(hdict['pattern'])


    def downloadFailed(self, pyfile):
        """remove plugin override if download fails but not if file is offline/temp.offline"""
        if pyfile.hasStatus("failed") and self.getConfig("revertfailed", True):
            hdict = self.core.pluginManager.plugins[self.type][pyfile.pluginname]
            if "new_name" in hdict and hdict['new_name'] == self.__name__:
                self.logDebug("Unload MultiHook", pyfile.pluginname, hdict)
                self.unloadPlugin(pyfile.pluginname)
                pyfile.setStatus("queued")
