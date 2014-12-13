# -*- coding: utf-8 -*-

import re

from pyload.plugin.Addon import Addon
from pyload.utils import remove_chars


class MultiHoster(Addon):
    __name    = "MultiHoster"
    __type    = "addon"
    __version = "0.20"

    __description = """Base multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("pyLoad Team", "admin@pyload.org")]


    HOSTER_REPLACEMENTS = [("1fichier.com", "onefichier.com"), ("2shared.com", "twoshared.com"),
                           ("4shared.com", "fourshared.com"), ("cloudnator.com", "shragle.com"),
                           ("easy-share.com", "crocko.com"), ("freakshare.net", "freakshare.com"),
                           ("hellshare.com", "hellshare.cz"), ("ifile.it", "filecloud.io"),
                           ("putlocker.com", "firedrive.com"), ("share-rapid.cz", "multishare.cz"),
                           ("sharerapid.cz", "multishare.cz"), ("ul.to", "uploaded.to"),
                           ("uploaded.net", "uploaded.to")]
    HOSTER_EXCLUDED     = []


    def setup(self):
        self.interval      = 12 * 60 * 60  #: reload hosters every 12h
        self.hosters       = []
        self.supported     = []
        self.new_supported = []


    def getConfig(self, option, default=''):
        """getConfig with default value - subclass may not implements all config options"""
        try:
            # Fixed loop due to getConf deprecation in 0.4.10
            return super(MultiHoster, self).getConfig(option)
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


    def activate(self):
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
        pluginMap    = dict((name.lower(), name) for name in self.core.pluginManager.hosterPlugins.keys())
        accountList  = [name.lower() for name, data in self.core.accountManager.accounts.iteritems() if data]
        excludedList = []

        for hoster in self.getHosterCached():
            name = remove_chars(hoster.lower(), "-.")

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

        module = self.core.pluginManager.getPlugin(self.__type, self.__name)
        klass  = getattr(module, self.__name)

        # inject plugin plugin
        self.logDebug("Overwritten Hosters", ", ".join(sorted(self.supported)))
        for hoster in self.supported:
            dict = self.core.pluginManager.hosterPlugins[hoster]
            dict['new_module'] = module
            dict['new_name']   = self.__name

        if excludedList:
            self.logInfo(_("The following hosters were not overwritten - account exists"), ", ".join(sorted(excludedList)))

        if self.new_supported:
            self.logDebug("New Hosters", ", ".join(sorted(self.new_supported)))

            # create new regexp
            regexp = r'.*(%s).*' % "|".join([x.replace(".", "\.") for x in self.new_supported])
            if hasattr(klass, "__pattern") and isinstance(klass.__pattern, basestring) and '://' in klass.__pattern:
                regexp = r'%s|%s' % (klass.__pattern, regexp)

            self.logDebug("Regexp", regexp)

            dict = self.core.pluginManager.hosterPlugins[self.__name]
            dict['pattern'] = regexp
            dict['re']      = re.compile(regexp)


    def unloadHoster(self, hoster):
        dict = self.core.pluginManager.hosterPlugins[hoster]
        if "module" in dict:
            del dict['module']

        if "new_module" in dict:
            del dict['new_module']
            del dict['new_name']


    def deactivate(self):
        """Remove override for all hosters. Scheduler job is removed by AddonManager"""
        for hoster in self.supported:
            self.unloadHoster(hoster)

        # reset pattern
        klass = getattr(self.core.pluginManager.getPlugin(self.__type, self.__name), self.__name)
        dict  = self.core.pluginManager.hosterPlugins[self.__name]
        dict['pattern'] = getattr(klass, "__pattern", r'^unmatchable$')
        dict['re']      = re.compile(dict['pattern'])


    def downloadFailed(self, pyfile):
        """remove plugin override if download fails but not if file is offline/temp.offline"""
        if pyfile.hasStatus("failed") and self.getConfig("unloadFailing", True):
            hdict = self.core.pluginManager.hosterPlugins[pyfile.pluginname]
            if "new_name" in hdict and hdict['new_name'] == self.__name:
                self.logDebug("Unload MultiHoster", pyfile.pluginname, hdict)
                self.unloadHoster(pyfile.pluginname)
                pyfile.setStatus("queued")
