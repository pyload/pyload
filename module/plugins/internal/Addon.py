# -*- coding: utf-8 -*-

import threading

from .misc import Periodical, isiterable
from .Plugin import Plugin


class Addon(Plugin):
    __name__ = "Addon"
    __type__ = "hook"  # @TODO: Change to `addon` in 0.4.10
    __version__ = "0.55"
    __status__ = "stable"

    __threaded__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Base addon plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def __init__(self, core, manager):
        self._init(core)

        #: `HookManager`
        self.manager = manager
        self.lock = threading.Lock()

        #: Automatically register event listeners for functions, attribute will be deleted dont use it yourself
        self.event_map = {}

        self.info['ip'] = None  # @TODO: Remove in 0.4.10

        #: Callback of periodical job task, used by HookManager
        self.periodical = Periodical(self, self.periodical_task)
        self.cb = self.periodical.cb  # @TODO: Recheck in 0.4.10

        self.init()
        self._init_events()  # @TODO: Remove in 0.4.10
        self.init_events()

    @property
    def activated(self):
        """
        Checks if addon is activated
        """
        return self.config.get('activated')

    #@TODO: Remove in 0.4.10
    def _log(self, level, plugintype, pluginname, messages):
        plugintype = "addon" if plugintype == "hook" else plugintype
        return Plugin._log(self, level, plugintype, pluginname, messages)

    #@TODO: Remove in 0.4.10
    def _init_events(self):
        event_map = {'allDownloadsFinished': "all_downloads_finished",
                     'allDownloadsProcessed': "all_downloads_processed",
                     'configChanged': "config_changed",
                     'download_processed': "download_processed",
                     'download_start': "download_start",
                     'linksAdded': "links_added",
                     'packageDeleted': "package_deleted",
                     'package_failed': "package_failed",
                     'package_processed': "package_processed"}
        for event, funcs in event_map.items():
            self.manager.addEvent(event, getattr(self, funcs))

    def init_events(self):
        if self.event_map:
            for event, funcs in self.event_map.items():
                if isiterable(funcs):
                    for f in funcs:
                        self.manager.addEvent(event, getattr(self, f))
                else:
                    self.manager.addEvent(event, getattr(self, funcs))

            #: Delete for various reasons
            self.event_map = None

    def periodical_task(self):
        raise NotImplementedError

    #: Deprecated method, use `activated` property instead (Remove in 0.4.10)
    def isActivated(self):
        return self.activated

    def deactivate(self):
        """
        Called when addon was deactivated
        """
        pass

    #: Deprecated method, use `deactivate` instead (Remove in 0.4.10)
    def unload(self):
        self.db.store("info", self.info)
        return self.deactivate()

    def activate(self):
        """
        Called when addon was activated
        """
        pass

    #: Deprecated method, use `activate` instead (Remove in 0.4.10)
    def coreReady(self):
        self.db.retrieve("info", self.info)
        return self.activate()

    def exit(self):
        """
        Called by core.shutdown just before pyLoad exit
        """
        pass

    #: Deprecated method, use `exit` instead (Remove in 0.4.10)
    def coreExiting(self):
        self.unload()  # @TODO: Fix in 0.4.10
        return self.exit()

    def config_changed(self, category, option, value, section):
        pass

    def all_downloads_finished(self):
        pass

    def all_downloads_processed(self):
        pass

    def links_added(self, urls, pypack):
        pass

    def download_preparing(self, pyfile):
        pass

    #: Deprecated method, use `download_preparing` instead (Remove in 0.4.10)
    def downloadPreparing(self, pyfile):
        if pyfile.plugin.req is not None:  # @TODO: Remove in 0.4.10
            return self.download_preparing(pyfile)

    def download_start(self, pyfile, url, filename):
        pass

    def download_processed(self, pyfile):
        pass

    def download_finished(self, pyfile):
        pass

    #: Deprecated method, use `download_finished` instead (Remove in 0.4.10)
    def downloadFinished(self, pyfile):
        return self.download_finished(pyfile)

    def download_failed(self, pyfile):
        pass

    #: Deprecated method, use `download_failed` instead (Remove in 0.4.10)
    def downloadFailed(self, pyfile):
        if pyfile.hasStatus(
                "failed"):  # @NOTE: Check if "still" set as failed (Fix in 0.4.10)
            return self.download_failed(pyfile)

    def package_processed(self, pypack):
        pass

    def package_deleted(self, pid):
        pass

    def package_failed(self, pypack):
        pass

    def package_finished(self, pypack):
        pass

    #: Deprecated method, use `package_finished` instead (Remove in 0.4.10)
    def packageFinished(self, pypack):
        return self.package_finished(pypack)

    def before_reconnect(self, ip):
        pass

    #: Deprecated method, use `before_reconnect` instead (Remove in 0.4.10)
    def beforeReconnecting(self, ip):
        return self.before_reconnect(ip)

    def after_reconnect(self, ip, oldip):
        pass

    #: Deprecated method, use `after_reconnect` instead (Remove in 0.4.10)
    def afterReconnecting(self, ip):
        self.after_reconnect(ip, self.info['ip'])
        self.info['ip'] = ip

    def captcha_task(self, task):
        """
        New captcha task for the plugin, it MUST set the handler and timeout or will be ignored
        """
        pass

    #: Deprecated method, use `captcha_task` instead (Remove in 0.4.10)
    def newCaptchaTask(self, task):
        return self.captcha_task(task)

    def captcha_correct(self, task):
        pass

    #: Deprecated method, use `captcha_correct` instead (Remove in 0.4.10)
    def captchaCorrect(self, task):
        return self.captcha_correct(task)

    def captcha_invalid(self, task):
        pass

    #: Deprecated method, use `captcha_invalid` instead (Remove in 0.4.10)
    def captchaInvalid(self, task):
        return self.captcha_invalid(task)
