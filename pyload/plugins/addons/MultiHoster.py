#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from random import choice

from pyload.plugins.MultiHoster import MultiHoster as MultiHosterAccount, normalize
from pyload.plugins.Addon import Addon, AddEventListener
from pyload.PluginManager import PluginMatcher


class MultiHoster(Addon, PluginMatcher):
    __version__ = "0.1"
    __internal__ = True
    __description__ = "Gives ability to use MultiHoster services."
    __config__ = []
    __author__ = ("pyLoad Team",)
    __author_mail__ = ("support@pyload.org",)

    #TODO: multiple accounts - multihoster / config options

    def init(self):
        # overwritten plugins mapped to list of multihoster
        self.plugins = {}

        # multihoster mapped to new regexp
        self.regexp = {}

    def matchURL(self, url):
        """ Overwritten to include new plugin regexp """
        for hoster, regexp in self.regexp.items():
            if regexp.search(url):
                return "hoster", hoster

    def matchPlugin(self, plugin, name):
        """ Overwritten to overwrite already supported plugins """

        # TODO: check if account is usable
        # TODO: multiuser

        # Chooses a random multi hoster plugin
        if name in self.plugins:
            return plugin, choice(self.plugins[name])

    def addHoster(self, account):

        self.logInfo(_("Activated %s") % account.__name__)

        pluginMap = {}
        for name in self.core.pluginManager.getPlugins("hoster").keys():
            pluginMap[name.lower()] = name

        supported = []
        new_supported = []

        for hoster in account.getHosterList():
            name = normalize(hoster)

            if name in pluginMap:
                supported.append(pluginMap[name])
            else:
                new_supported.append(hoster)

        if not supported and not new_supported:
            account.logError(_("No Hoster loaded"))
            return

        klass = self.core.pluginManager.getPluginClass("hoster", account.__name__, overwrite=False)

        if not klass:
            return

        # inject plugin plugin
        account.logDebug("Overwritten Hosters: %s" % ", ".join(sorted(supported)))
        for hoster in supported:
            if hoster in self.plugins:
                self.plugins[hoster].append(klass.__name__)
            else:
                self.plugins[hoster] = [klass.__name__]

        account.logDebug("New Hosters: %s" % ", ".join(sorted(new_supported)))

        # create new regexp
        patterns = [x.replace(".", "\\.") for x in new_supported]

        if klass.__pattern__:
            patterns.append(klass.__pattern__)

        self.regexp[klass.__name__] = re.compile(r".*(%s).*" % "|".join(patterns))


    @AddEventListener(["account:deleted", "account:updated"])
    def refreshAccounts(self, plugin=None, loginname=None, user=None):
        self.logDebug("Re-checking accounts")

        self.plugins = {}
        for plugin, account in self.core.accountManager.iterAccounts():
            if isinstance(account, MultiHosterAccount) and account.isUsable():
                self.addHoster(account)

    @AddEventListener("account:loaded")
    def refreshAccount(self, acc):

        account = self.core.accountManager.getAccount(acc.plugin, acc.loginname)
        if isinstance(account, MultiHosterAccount) and account.isUsable():
            self.addHoster(account)

    def activate(self):
        self.refreshAccounts()
        self.core.pluginManager.addMatcher(self)

    def deactivate(self):
        self.core.pluginManager.removeMatcher(self)
