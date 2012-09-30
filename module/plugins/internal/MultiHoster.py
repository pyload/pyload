#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.utils import remove_chars
from module.plugins.Hook import Hook

class MultiHoster(Hook):
    """
    Generic MultiHoster plugin
    """

    __version__ = "0.16"

    interval = 0
    replacements = [("2shared.com", "twoshared.com"), ("4shared.com", "fourshared.com"), ("cloudnator.com", "shragle.com"),
                    ("ifile.it", "filecloud.io"), ("easy-share.com","crocko.com"), ("freakshare.net","freakshare.com"),
                    ("hellshare.com", "hellshare.cz"), ("share-rapid.cz","sharerapid.com"), ("sharerapid.cz","sharerapid.com"),
                    ("ul.to","uploaded.to"), ("uploaded.net","uploaded.to")]
    ignored = []
    
    def setup(self):
        self.hosters = []
        self.supported = []
        self.new_supported = []

    def getHosterCached(self):
        if not self.hosters:

            try:
                hosterSet = self.toHosterSet(self.getHoster()) - set(self.ignored)
            except Exception, e:
                self.logError("%s" % str(e))
                return []
                
            try: 
                configMode = self.getConfig('hosterListMode')
                if configMode in ("listed", "unlisted"):
                    configSet = self.toHosterSet(self.getConfig('hosterList').replace('|',',').replace(';',',').split(','))
                    
                    if configMode == "listed":
                        hosterSet &= configSet
                    else:
                        hosterSet -= configSet
                                
            except Exception, e:
                self.logError("%s" % str(e))
        
            self.hosters = list(hosterSet)

        return self.hosters
        
    def toHosterSet(self, hosters):
        hosters = set((x.strip().lower() for x in hosters))
    
        for rep in self.replacements:
            if rep[0] in hosters:
                hosters.remove(rep[0])
                hosters.add(rep[1])
        
        hosters.discard(u'')        
        return hosters

    def getHoster(self):
        """Load list of supported hoster

        :return: List of domain names
        """
        raise NotImplementedError

    def coreReady(self):
        pluginMap = {}
        for name in self.core.pluginManager.hosterPlugins.keys():
            pluginMap[name.lower()] = name
        
        accountList = [ name.lower() for name, data in self.core.accountManager.accounts.items() if data ]
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

        module = self.core.pluginManager.getPlugin(self.__name__)
        klass = getattr(module, self.__name__)
        
        print module, klass

        # inject plugin plugin
        self.logDebug("Overwritten Hosters: %s" % ", ".join(sorted(self.supported)))
        for hoster in self.supported:
            dict = self.core.pluginManager.hosterPlugins[hoster]
            dict["new_module"] = module
            dict["new_name"] = self.__name__
            
        if excludedList:
            self.logInfo("The following hosters were not overwritten - account exists: %s" % ", ".join(sorted(excludedList)))

        if self.new_supported:
            self.logDebug("New Hosters: %s" % ", ".join(sorted(self.new_supported)))
    
            # create new regexp
            if not klass.__pattern__:
                regexp = r".*(%s).*" % "|".join([x.replace(".", "\\.") for x in new_supported])
            else:
                regexp = r"%s|.*(%s).*" % (klass.__pattern__, "|".join([x.replace(".", "\\.") for x in self.new_supported]))
            self.logDebug("Regexp: %s" % regexp)
    
            dict = self.core.pluginManager.hosterPlugins[self.__name__]
            dict["pattern"] = regexp
            dict["re"] = re.compile(regexp)


    def unloadHoster(self, hoster):
        dict = self.core.pluginManager.hosterPlugins[hoster]
        if "module" in dict:
            del dict["module"]

        if "new_module" in dict:
            del dict["new_module"]
            del dict["new_name"]

    def unload(self):
        for hoster in self.supported:
            self.unloadHoster(hoster)    
            
    def downloadFailed(self, pyfile):
        """remove plugin override if download fails but not if file is offline/temp.offline"""  
        if pyfile.hasStatus("failed"):
            hdict = self.core.pluginManager.hosterPlugins[pyfile.pluginname]
            self.logDebug("Unload MultiHoster", pyfile.pluginname, hdict)
            if "new_name" in hdict and hdict['new_name'] == self.__name__:    
                self.unloadHoster(pyfile.pluginname)
                pyfile.setStatus("queued")