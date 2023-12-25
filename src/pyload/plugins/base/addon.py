# -*- coding: utf-8 -*-

import threading
from functools import wraps

from pyload.core.utils.check import is_sequence

from ..helpers import Periodical
from .plugin import BasePlugin


def threaded(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return self.pyload.adm.start_thread(func, self, *args, **kwargs)

    return wrapper


# NOTE: Performance penalty than original 'Expose' class decorator :(
def expose(func):
    """
    Used for decoration to declare rpc services.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not wrapper._exposed:
            self.pyload.adm.add_rpc(func.__module__, func.__name__, func.__doc__)
            wrapper._exposed = True
        return func(self, *args, **kwargs)

    wrapper._exposed = False
    return wrapper


class BaseAddon(BasePlugin):
    __name__ = "BaseAddon"
    __type__ = "addon"
    __version__ = "0.56"
    __status__ = "stable"

    __description__ = """Base addon plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def __init__(self, core, manager):
        self._init(core)

        #: `AddonManager`
        self.m = self.manager = manager
        self.lock = threading.Lock()

        #: Automatically register event listeners for functions, attribute will be deleted dont use it yourself
        self.event_map = {}

        #: Callback of periodical job task, used by AddonManager
        self.periodical = Periodical(self, self.periodical_task)
        self.cb = self.periodical.cb  # TODO: Recheck in 0.6.x

        self.init()
        self._init_events()  # TODO: Remove in 0.6.x
        self.init_events()

    @property
    def activated(self):
        """
        Checks if addon is activated.
        """
        return self.config.get("enabled")

    # TODO: Remove in 0.6.x
    def _init_events(self):
        event_map = {
            "all_downloads_finished": "all_downloads_finished",
            "all_downloads_processed": "all_downloads_processed",
            "config_changed": "config_changed",
            "download_processed": "download_processed",
            "download_start": "download_start",
            "links_added": "links_added",
            "package_deleted": "package_deleted",
            "package_failed": "package_failed",
            "package_processed": "package_processed",
        }
        for event, funcs in event_map.items():
            self.m.add_event(event, getattr(self, funcs))

    def init_events(self):
        if self.event_map:
            for event, funcs in self.event_map.items():
                if not is_sequence(funcs):
                    funcs = [funcs]
                for fn in funcs:
                    self.m.add_event(event, getattr(self, fn))

            #: Delete for various reasons
            self.event_map = None

    def periodical_task(self):
        raise NotImplementedError

    #: Deprecated method, use `enabled` property instead (Remove in 0.6.x)
    def is_activated(self):
        return self.activated

    def deactivate(self):
        """
        Called when addon was deactivated.
        """
        pass

    #: Deprecated method, use `deactivate` instead (Remove in 0.6.x)
    def unload(self):
        self.db.store("info", self.info)
        return self.deactivate()

    def activate(self):
        """
        Called when addon was activated.
        """
        pass

    #: Deprecated method, use `activate` instead (Remove in 0.6.x)
    def core_ready(self):
        self.db.retrieve("info", self.info)
        return self.activate()

    def exit(self):
        """
        Called by core.shutdown just before pyLoad exit.
        """
        pass

    #: Deprecated method, use `exit` instead (Remove in 0.6.x)
    def core_exiting(self):
        self.unload()  # TODO: Fix in 0.6.x
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

    #: Deprecated method, use `download_preparing` instead (Remove in 0.6.x)
    # def download_preparing(self, pyfile):
    #     if pyfile.plugin.req is not None:  # TODO: Remove in 0.6.x
    #         return self.download_preparing(pyfile)

    def download_start(self, pyfile, url, filename):
        pass

    def download_processed(self, pyfile):
        pass

    def download_finished(self, pyfile):
        pass

    def download_failed(self, pyfile):
        pass

    def package_processed(self, pypack):
        pass

    def package_deleted(self, pid):
        pass

    def package_failed(self, pypack):
        pass

    def package_finished(self, pypack):
        pass

    def before_reconnect(self, ip):
        pass

    def after_reconnect(self, ip, old_ip):
        pass

    def captcha_task(self, task):
        """
        New captcha task for the plugin, it MUST set the handler and timeout or will be
        ignored.
        """
        pass

    def captcha_correct(self, task):
        pass

    def captcha_invalid(self, task):
        pass
