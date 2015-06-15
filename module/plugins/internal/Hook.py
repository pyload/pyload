# -*- coding: utf-8 -*-

import traceback

from module.plugins.internal.Plugin import Plugin


class Expose(object):
    """Used for decoration to declare rpc services"""

    def __new__(cls, f, *args, **kwargs):
        hookManager.addRPC(f.__module__, f.func_name, f.func_doc)
        return f


def threaded(fn):

    def run(*args, **kwargs):
        hookManager.startThread(fn, *args, **kwargs)

    return run


class Hook(Plugin):
    __name__    = "Hook"
    __type__    = "hook"
    __version__ = "0.08"

    __config__   = []  #: [("name", "type", "desc", "default")]
    __threaded__ = []  #@TODO: Remove in 0.4.10

    __description__ = """Base hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "RaNaN@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, core, manager):
        super(Hook, self).__init__(core)

        #: `HookManager`
        self.manager = manager

        #: Provide information in dict here, usable by API `getInfo`
        self.info = {}

        #: automatically register event listeners for functions, attribute will be deleted dont use it yourself
        self.event_map = {}

        # Deprecated alternative to event_map
        #: List of events the plugin can handle, name the functions exactly like eventname.
        self.event_list = []  #@NOTE: dont make duplicate entries in event_map

        #: Callback of periodical job task, used by HookManager
        self.cb       = None
        self.interval = 60

        self.setup()
        self.init_events()
        self.init_periodical(10)


    def init_events(self):
        if self.event_map:
            for event, funcs in self.event_map.iteritems():
                if type(funcs) in (list, tuple):
                    for f in funcs:
                        self.manager.addEvent(event, getattr(self, f))
                else:
                    self.manager.addEvent(event, getattr(self, funcs))

            # delete for various reasons
            self.event_map = None

        if self.event_list:
            self.logDebug("Deprecated method `event_list`, use `event_map` instead")

            for f in self.event_list:
                self.manager.addEvent(f, getattr(self, f))

            self.event_list = None


    def init_periodical(self, delay=0, threaded=False):
        self.cb = self.core.scheduler.addJob(max(0, delay), self._periodical, [threaded], threaded=threaded)


    #: Deprecated method, use `init_periodical` instead
    def initPeriodical(self):
        return self.init_periodical()


    def _periodical(self, threaded):
        if self.interval < 0:
            self.cb = None
            return

        try:
            self.periodical()

        except Exception, e:
            self.logError(_("Error executing hook: %s") % e)
            if self.core.debug:
                traceback.print_exc()

        self.cb = self.core.scheduler.addJob(self.interval, self._periodical, [threaded], threaded=threaded)


    def periodical(self):
        pass


    def __repr__(self):
        return "<Hook %s>" % self.__name__


    def setup(self):
        """More init stuff if needed"""
        pass


    def is_activated(self):
        """Checks if hook is activated"""
        return self.getConfig("activated")


    #: Deprecated method, use `is_activated` instead
    def isActivated(self):
        return self.is_activated()


    def deactivate(self):
        """Called when hook was deactivated"""
        pass


    #: Deprecated method, use `deactivate` instead
    def unload(self):
        return self.deactivate()


    def activate(self):
        """Called when hook was activated"""
        pass


    #: Deprecated method, use `activate` instead
    def coreReady(self):
        return self.activate()


    def exit(self):
        """Called by core.shutdown just before pyLoad exit"""
        pass


    #: Deprecated method, use `exit` instead
    def coreExiting(self):
        return self.exit()


    def download_preparing(self, pyfile):
        pass


    #: Deprecated method, use `download_preparing` instead
    def downloadPreparing(self, pyfile):
        return self.download_preparing(pyfile)


    def download_finished(self, pyfile):
        pass


    #: Deprecated method, use `download_finished` instead
    def downloadFinished(self, pyfile):
        return self.download_finished(pyfile)


    def download_failed(self, pyfile):
        pass


    #: Deprecated method, use `download_failed` instead
    def downloadFailed(self, pyfile):
        return self.download_failed(pyfile)


    def package_finished(self, pypack):
        pass


    #: Deprecated method, use `package_finished` instead
    def packageFinished(self, pypack):
        return self.package_finished(pypack)


    def before_reconnect(self, ip):
        pass


    #: Deprecated method, use `before_reconnect` instead
    def beforeReconnecting(self, ip):
        return self.before_reconnect(ip)


    def after_reconnect(self, ip, oldip):
        pass


    #: Deprecated method, use `after_reconnect` instead
    def afterReconnecting(self, ip):
        return self.after_reconnect(ip, None)


    def captcha_task(self, task):
        """New captcha task for the plugin, it MUST set the handler and timeout or will be ignored"""
        pass


    #: Deprecated method, use `captcha_task` instead
    def newCaptchaTask(self, task):
        return self.captcha_task(task)


    def captcha_correct(self, task):
        pass


    #: Deprecated method, use `captcha_correct` instead
    def captchaCorrect(self, task):
        return self.captcha_correct(task)


    def captcha_invalid(self, task):
        pass


    #: Deprecated method, use `captcha_invalid` instead
    def captchaInvalid(self, task):
        return self.captcha_invalid(task)
