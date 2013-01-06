#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.database import DatabaseMethods, queue, async

class ConfigMethods(DatabaseMethods):

    @async
    def saveConfig(self, plugin, config, user=None):
        if user is None:
            self.c.execute('INSERT INTO settings(plugin, config) VALUES(?,?)', (plugin, config))
        else:
            self.c.execute('INSERT INTO settings(plugin, config, user) VALUES(?,?,?)', (plugin, config, user))


    @queue
    def loadConfig(self, plugin, user=None):
        if user is None:
            self.c.execute('SELECT config FROM settings WHERE plugin=? AND user=-1', (plugin, ))
        else:
            self.c.execute('SELECT config FROM settings WHERE plugin=? AND user=?', (plugin, user))

        r = self.c.fetchone()
        return r[0] if r else ""

    @async
    def deleteConfig(self, plugin, user=None):
        if user is None:
            self.c.execute('DELETE FROM settings WHERE plugin=?', (plugin, ))
        else:
            self.c.execute('DELETE FROM settings WHERE plugin=? AND user=?', (plugin, user))

    @queue
    def loadAllConfigs(self):
        self.c.execute('SELECT user, plugin, config FROM settings')
        configs = {}
        for r in self.c:
            if r[0] in configs:
                configs[r[0]][r[1]] = r[2]
            else:
                configs[r[0]] = {r[1]: r[2]}

        return configs

    @queue
    def loadConfigsForUser(self, user=None):
        if user is None: user = -1
        self.c.execute('SELECT plugin, config FROM settings WHERE user=?', (user,))
        configs = {}
        for r in self.c:
            configs[r[0]] = r[1]

        return configs

    @async
    def clearAllConfigs(self):
        self.c.execute('DELETE FROM settings')


ConfigMethods.register()