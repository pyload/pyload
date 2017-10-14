# -*- coding: utf-8 -*-

import time

from .Addon import Addon
from .misc import Expose, encode, isiterable


class Notifier(Addon):
    __name__ = "Notifier"
    __type__ = "hook"
    __version__ = "0.11"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("captcha", "bool", "Notify captcha request", True),
                  ("reconnection", "bool", "Notify reconnection request", False),
                  ("downloadfinished", "bool", "Notify download finished", True),
                  ("downloadfailed", "bool", "Notify download failed", True),
                  ("packagefinished", "bool", "Notify package finished", True),
                  ("packagefailed", "bool", "Notify package failed", True),
                  ("update", "bool", "Notify pyLoad update", False),
                  ("exit", "bool", "Notify pyLoad shutdown/restart", False),
                  ("sendinterval", "int",
                   "Interval in seconds between notifications", 1),
                  ("sendpermin", "int", "Max notifications per minute", 60),
                  ("ignoreclient", "bool", "Send notifications if client is connected", True)]

    __description__ = """Base notifier plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def init(self):
        self.event_map = {'allDownloadsProcessed': "all_downloads_processed",
                          'pyload_updated': "pyload_updated"}

        self.last_notify = 0
        self.notifications = 0

    def get_key(self):
        raise NotImplementedError

    def send(self, event, msg, key):
        raise NotImplementedError

    def pyload_updated(self, etag):
        if not self.config.get('update', True):
            return

        self.notify(_("pyLoad updated"), etag)

    def exit(self):
        if not self.config.get('exit', True):
            return

        if self.pyload.do_restart:
            self.notify(_("Restarting pyLoad"))
        else:
            self.notify(_("Exiting pyLoad"))

    def captcha_task(self, task):
        if not self.config.get('captcha', True):
            return

        self.notify(_("Captcha"), _("New request waiting user input"))

    def before_reconnect(self, ip):
        if not self.config.get('reconnection', False):
            return

        self.notify(_("Waiting reconnection"), _("Current IP: %s") % ip)

    def after_reconnect(self, ip, oldip):
        if not self.config.get('reconnection', False):
            return

        self.notify(_("Reconnection failed"), _("Current IP: %s") % ip)

    def package_finished(self, pypack):
        if not self.config.get('packagefinished', True):
            return

        self.notify(_("Package finished"), pypack.name)

    def package_failed(self, pypack):
        if not self.config.get('packagefailed', True):
            return

        self.notify(_("Package failed"), pypack.name)

    def download_finished(self, pyfile):
        if not self.config.get('downloadfinished', False):
            return

        self.notify(_("Download finished"), pyfile.name)

    def download_failed(self, pyfile):
        if self.config.get('downloadfailed', True):
            return

        self.notify(_("Download failed"), pyfile.name)

    def all_downloads_processed(self):
        self.notify(_("All downloads processed"))

    def all_downloads_finished(self):
        self.notify(_("All downloads finished"))

    @Expose
    def notify(self, event, msg=None, key=None):
        key = key or self.get_key()
        if not key or isiterable(key) and not all(key):
            return

        if isiterable(msg):
            msg = " | ".join(encode(a).strip() for a in msg if a)
        else:
            msg = encode(msg)

        if self.pyload.isClientConnected() and not self.config.get('ignoreclient', False):
            return

        elapsed_time = time.time() - self.last_notify

        if elapsed_time < self.config.get('sendinterval', 1):
            return

        elif elapsed_time > 60:
            self.notifications = 0

        elif self.notifications >= self.config.get('sendpermin', 60):
            return

        self.log_debug("Sending notification...")

        try:
            self.send(event, msg, key)

        except Exception, e:
            self.log_error(_("Error sending notification"), e)
            return False

        else:
            self.log_debug("Notification sent")
            return True

        finally:
            self.last_notify = time.time()
            self.notifications += 1
