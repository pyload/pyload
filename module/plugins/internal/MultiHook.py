# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook
from module.utils import remove_chars


class MultiHook(Hook):
    __name__    = "MultiHook"
    __type__    = "hook"
    __version__ = "0.22"

    __description__ = """Hook plugin for MultiHoster"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    interval = 12 * 60 * 60  #: reload hosters every 12h

    HOSTER_REPLACEMENTS = [("1fichier.com"   , "onefichier.com"),
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
    HOSTER_EXCLUDED     = []


    def setup(self):
        self.hosters       = []
        self.supported     = []
        self.new_supported = []


    def getConfig(self, option, default=''):
        """getConfig with default value - sublass may not implements all config options"""
        try:
            return self.getConf(option)
        except KeyError:
            return default


    def getHosterCached(self):
        if not self.hosters:
            try:
                hosterSet = self.toHosterSet(self.getHoster()) - set(self.HOSTER_EXCLUDED)
            except Exception, e:
                self.logError(e)
                return []

            try:
                configMode = self.getConfig('hosterListMode', 'all')
                if configMode in ("listed", "unlisted"):
                    configSet = self.toHosterSet(self.getConfig('hosterList', '').replace('|', ',').replace(';', ',').split(','))

                    if configMode == "listed":
                        hosterSet &= configSet
                    else:
                        hosterSet -= configSet

            except Exception, e:
                self.logError(e)

            self.hosters = list(hosterSet)

        return self.hosters


    def toHosterSet(self, hosters):
        hosters = set((str(x).strip().lower() for x in hosters))

        for rep in self.HOSTER_REPLACEMENTS:
            if rep[0] in hosters:
                hosters.remove(rep[0])
                hosters.add(rep[1])

        hosters.discard('')
        return hosters


    def getHoster(self):
        """Load list of supported hoster

        :return: List of domain names
        """
        raise NotImplementedError


    def coreReady(self):
        if self.cb:
            self.core.scheduler.removeJob(self.cb)

        self.setConfig("activated", True)  #: config not in sync after plugin reload

        cfg_interval = self.getConfig("interval", None)  #: reload interval in hours
        if cfg_interval is not None:
            self.interval = cfg_interval * 60 * 60

        if self.interval:
            self._periodical()
        else:
            self.periodical()


    def initPeriodical(self):
        pass


    def periodical(self):
        """reload hoster list periodically"""
        self.logInfo(_("Reloading supported hoster list"))

        old_supported      = self.supported
        self.supported     = []
        self.new_supported = []
        self.hosters       = []

        self.overridePlugins()

        old_supported = [hoster for hoster in old_supported if hoster not in self.supported]
        if old_supported:
            self.logDebug("UNLOAD", ", ".join(old_supported))
            for hoster in old_supported:
                self.unloadHoster(hoster)


    def overridePlugins(self):
        pluginMap    = dict((name.lower(), name) for name in self.core.pluginManager.hosterPlugins.iterkeys())
        accountList  = [name.lower() for name, data in self.core.accountManager.accounts.iteritems() if data]
        excludedList = []

        for hoster in self.getHosterCached():
            name = remove_chars(hoster, "-.")

            if name in accountList:
                excludedList.append(hoster)
            else:
                if name in pluginMap:
                    self.supported.append(pluginMap[name])
                else:
                    self.new_supported.append(hoster)

        if not self.supported and not self.new_supported:
            self.logError(_("No Hoster loaded"))
            return

        module = self.core.pluginManager.getPlugin(self.__name__)
        klass  = getattr(module, self.__name__)

        # inject plugin plugin
        self.logDebug("Overwritten Hosters", ", ".join(sorted(self.supported)))
        for hoster in self.supported:
            hdict = self.core.pluginManager.hosterPlugins[hoster]
            hdict['new_module'] = module
            hdict['new_name']   = self.__name__

        if excludedList:
            self.logInfo(_("The following hosters were not overwritten - account exists"), ", ".join(sorted(excludedList)))

        if self.new_supported:
            hosters = sorted(self.new_supported)

            self.logDebug("New Hosters", ", ".join(hosters))

            # create new regexp
            regexp = r'.*(%s).*' % "|".join([x.replace(".", "\.") for x in hosters])
            if hasattr(klass, "__pattern__") and isinstance(klass.__pattern__, basestring) and '://' in klass.__pattern__:
                regexp = r'%s|%s' % (klass.__pattern__, regexp)

            self.logDebug("Regexp", regexp)

            hdict = self.core.pluginManager.hosterPlugins[self.__name__]
            hdict['pattern'] = regexp
            hdict['re']      = re.compile(regexp)


    def unloadHoster(self, hoster):
        hdict = self.core.pluginManager.hosterPlugins[hoster]
        if "module" in hdict:
            del hdict['module']

        if "new_module" in hdict:
            del hdict['new_module']
            del hdict['new_name']


    def unload(self):
        """Remove override for all hosters. Scheduler job is removed by hookmanager"""
        for hoster in self.supported:
            self.unloadHoster(hoster)

        # reset pattern
        klass = getattr(self.core.pluginManager.getPlugin(self.__name__), self.__name__)
        hdict  = self.core.pluginManager.hosterPlugins[self.__name__]
        hdict['pattern'] = getattr(klass, "__pattern__", r'^unmatchable$')
        hdict['re']      = re.compile(hdict['pattern'])


    def downloadFailed(self, pyfile):
        """remove plugin override if download fails but not if file is offline/temp.offline"""
        if pyfile.hasStatus("failed") and self.getConfig("unloadFailing", True):
            hdict = self.core.pluginManager.hosterPlugins[pyfile.pluginname]
            if "new_name" in hdict and hdict['new_name'] == self.__name__:
                self.logDebug("Unload MultiHook", pyfile.pluginname, hdict)
                self.unloadHoster(pyfile.pluginname)
                pyfile.setStatus("queued")
