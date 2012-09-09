#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.database import DatabaseMethods, queue, async, inner

# TODO

class ConfigMethods(DatabaseMethods):

    @async
    def saveConfig(self, plugin, user, config):
        pass

    @queue
    def loadConfig(self, plugin, user):
        pass

    @async
    def deleteConfig(self, plugin, user):
        pass

    @queue
    def loadAllConfigs(self):
        pass



ConfigMethods.register()