#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.utils import remove_chars
from module.plugins.Hook import Hook
from module.plugins.PluginManager import PluginTuple

class MultiHoster(Hook):
    """
    Generic MultiHoster plugin
    """

    interval = 0
    hosters = []
    replacements = []
    supported = []

    def getHosterCached(self):
        if not self.hosters:

            try:
                self.hosters = self.getHoster()
            except Exception, e:
                self.logError("%s" % str(e))
                return []

            for rep in self.replacements:
                if rep[0] in self.hosters:
                    self.hosters.remove(rep[0])
                    if rep[1] not in self.hosters:
                        self.hosters.append(rep[1])

        return self.hosters


    def getHoster(self):
        """Load list of supported hoster

        :return: List of domain names
        """
        raise NotImplementedError

    def coreReady(self):
        pluginMap = {}
        for name in self.core.pluginManager.getPlugins("hoster").keys():
            pluginMap[name.lower()] = name

        new_supported = []

        for hoster in self.getHosterCached():
            name = remove_chars(hoster.lower(), "-.")

            if name in pluginMap:
                self.supported.append(pluginMap[name])
            else:
                new_supported.append(hoster)

        if not self.supported and not new_supported:
            self.logError(_("No Hoster loaded"))
            return

        module = self.core.pluginManager.getPlugin(self.__name__)
        klass = getattr(module, self.__name__)

        # inject plugin plugin
        self.logDebug("Overwritten Hosters: %s" % ", ".join(sorted(self.supported)))
        for hoster in self.supported:
            self.core.pluginManager.injectPlugin("hoster", hoster, module, self.__name__)

        self.logDebug("New Hosters: %s" % ", ".join(sorted(new_supported)))

        # create new regexp
        regexp = r".*(%s).*" % "|".join([klass.__pattern__] + [x.replace(".", "\\.") for x in new_supported])

        hoster = self.core.pluginManager.getPlugins("hoster")
        p = hoster[self.__name__]
        new = PluginTuple(p.version, re.compile(regexp), p.deps, p.user, p.path)
        hoster[self.__name__] = new


    def deactivate(self):
        for hoster in self.supported:
            self.core.pluginManager.restoreState("hoster", hoster)