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
    __version__ = "0.03"

    __config__ = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "RaNaN@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, core, manager):
        #: Provide information in dict here, usable by API `getInfo`
        self.info = {}

        #: Callback of periodical job task, used by HookManager
        self.cb       = None
        self.interval = 60

        #: `HookManager`
        self.manager = manager

        self.setup()

        #: automatically register event listeners for functions, attribute will be deleted dont use it yourself
        self.event_map = {}

        # Deprecated alternative to event_map
        #: List of events the plugin can handle, name the functions exactly like eventname.
        self.event_list = []  #@NOTE: dont make duplicate entries in event_map

        # register events
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
            self.logWarning(_("Deprecated method `event_list`, use `event_map` instead"))

            for f in self.event_list:
                self.manager.addEvent(f, getattr(self, f))

            self.event_list = None


    def initPeriodical(self, delay=0, threaded=False):
        self.cb = self.core.scheduler.addJob(max(0, delay), self._periodical, [threaded], threaded=threaded)


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


    def __repr__(self):
        return "<Hook %s>" % self.__name__


    def setup(self):
        """More init stuff if needed"""
        pass


    def isActivated(self):
        """Checks if hook is activated"""
        return self.getConfig("activated")


    def deactivate(self):
        """Called when hook was deactivated"""
        pass


    #: Deprecated, use method `deactivate` instead
    def unload(self):
        self.logWarning(_("Deprecated method `unload`, use `deactivate` instead"))
        return self.deactivate()


    def activate(self):
        """Called when hook was activated"""
        pass


    #: Deprecated, use method `activate` instead
    def coreReady(self):
        self.logWarning(_("Deprecated method `coreReady`, use `activate` instead"))
        return self.activate()


    def exit(self):
        """Called by core.shutdown just before pyLoad exit"""
        pass


    #: Deprecated, use method `exit` instead
    def coreExiting(self):
        self.logWarning(_("Deprecated method `coreExiting`, use `exit` instead"))
        return self.exit()


    def downloadPreparing(self, pyfile):
        pass


    def downloadFinished(self, pyfile):
        pass


    def downloadFailed(self, pyfile):
        pass


    def packageFinished(self, pypack):
        pass


    def beforeReconnecting(self, ip):
        pass


    def afterReconnecting(self, ip):
        pass


    def periodical(self):
        pass


    def captchaTask(self, task):
        """New captcha task for the plugin, it MUST set the handler and timeout or will be ignored"""
        pass


    #: Deprecated, use method `captchaTask` instead
    def newCaptchaTask(self, task):
        self.logWarning(_("Deprecated method `newCaptchaTask`, use `captchaTask` instead"))
        return self.captchaTask()


    def captchaCorrect(self, task):
        pass


    def captchaInvalid(self, task):
        pass
