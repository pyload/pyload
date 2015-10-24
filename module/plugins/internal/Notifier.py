# -*- coding: utf-8 -*-

import time

from module.plugins.internal.Addon import Addon, Expose
from module.plugins.internal.utils import isiterable


class Notifier(Addon):
    __name__    = "Notifier"
    __type__    = "hook"
    __version__ = "0.04"
    __status__  = "testing"

    __config__ = [("activated"      , "bool", "Activated"                                , False),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify packages processed"                , True ),
                  ("notifyupdate"   , "bool", "Notify plugin updates"                    , True ),
                  ("notifyexit"     , "bool", "Notify pyLoad shutdown"                   , True ),
                  ("sendtimewait"   , "int" , "Timewait in seconds between notifications", 5    ),
                  ("sendpermin"     , "int" , "Max notifications per minute"             , 12   ),
                  ("ignoreclient"   , "bool", "Send notifications if client is connected", False)]

    __description__ = """Base notifier plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        self.event_map = {'allDownloadsProcessed': "all_downloads_processed",
                          'plugin_updated'       : "plugin_updated"         }

        self.last_notify   = 0
        self.notifications = 0


    def plugin_updated(self, type_plugins):
        if not self.get_config('notifyupdate'):
            return

        self.notify(_("Plugins updated"), str(type_plugins))


    def exit(self):
        if not self.get_config('notifyexit'):
            return

        if self.pyload.do_restart:
            self.notify(_("Restarting pyLoad"))
        else:
            self.notify(_("Exiting pyLoad"))


    def captcha_task(self, task):
        if not self.get_config('notifycaptcha'):
            return

        self.notify(_("Captcha"), _("New request waiting user input"))


    def package_finished(self, pypack):
        if self.get_config('notifypackage'):
            self.notify(_("Package finished"), pypack.name)


    def all_downloads_processed(self):
        if not self.get_config('notifyprocessed'):
            return

        if any(True for pdata in self.pyload.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            self.notify(_("Package failed"), _("One or more packages was not completed successfully"))
        else:
            self.notify(_("All packages finished"))


    def get_key(self):
        raise NotImplementedError


    def send(self, event, msg, key):
        raise NotImplementedError


    @Expose
    def notify(self, event, msg="", key=None):
        key = key or self.get_key()
        if not key or isiterable(key) and not all(key):
            return

        if self.pyload.isClientConnected() and not self.get_config('ignoreclient'):
            return

        elapsed_time = time.time() - self.last_notify

        if elapsed_time < self.get_config("sendtimewait"):
            return

        elif elapsed_time > 60:
            self.notifications = 0

        elif self.notifications >= self.get_config("sendpermin"):
            return

        self.log_info(_("Sending notification..."))

        try:
            resp = self.send(event, msg, key)

        except Exception, e:
            self.log_error(_("Error sending notification"), e)
            return False

        else:
            return True

        finally:
            self.last_notify = time.time()
            self.notifications += 1
