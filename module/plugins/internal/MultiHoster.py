#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.utils import remove_chars
from module.plugins.Hook import Hook

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
        for name in self.core.pluginManager.hosterPlugins.keys():
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
            dict = self.core.pluginManager.hosterPlugins[hoster]
            dict["new_module"] = module
            dict["new_name"] = self.__name__

        self.logDebug("New Hosters: %s" % ", ".join(sorted(new_supported)))

        # create new regexp
        regexp = r".*(%s).*" % "|".join([klass.__pattern__] + [x.replace(".", "\\.") for x in new_supported])

        dict = self.core.pluginManager.hosterPlugins[self.__name__]
        dict["pattern"] = regexp
        dict["re"] = re.compile(regexp)


    def unload(self):
        for hoster in self.supported:
            dict = self.core.pluginManager.hosterPlugins[hoster]
            if "module" in dict:
                del dict["module"]

            del dict["new_module"]
            del dict["new_name"]