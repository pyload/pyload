# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from .backend import DatabaseMethods, async, queue

standard_library.install_aliases()


class ConfigMethods(DatabaseMethods):

    @async
    def save_config(self, plugin, config, user=None):
        if user is None:
            user = -1
        self.c.execute(
            'INSERT INTO settings(plugin, config, user) VALUES(?,?,?)',
            (plugin, config, user))

    @queue
    def load_config(self, plugin, user=None):
        if user is None:
            user = -1
        self.c.execute(
            'SELECT config FROM settings WHERE plugin=? AND user=?',
            (plugin, user))

        r = self.c.fetchone()
        return r[0] if r else ""

    @async
    def delete_config(self, plugin, user=None):
        if user is None:
            self.c.execute('DELETE FROM settings WHERE plugin=?', (plugin,))
        else:
            self.c.execute(
                'DELETE FROM settings WHERE plugin=? AND user=?',
                (plugin, user))

    @queue
    def load_all_configs(self):
        self.c.execute('SELECT user, plugin, config FROM settings')
        configs = {}
        for r in self.c.fetchall():
            if r[0] in configs:
                configs[r[0]][r[1]] = r[2]
            else:
                configs[r[0]] = {r[1]: r[2]}

        return configs

    @queue
    def load_configs_for_user(self, user=None):
        if user is None:
            user = -1
        self.c.execute(
            'SELECT plugin, config FROM settings WHERE user=?', (user,))
        configs = {}
        for r in self.c.fetchall():
            configs[r[0]] = r[1]

        return configs

    @async
    def clear_all_configs(self):
        self.c.execute('DELETE FROM settings')


ConfigMethods.register()
