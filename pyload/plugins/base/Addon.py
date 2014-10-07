# -*- coding: utf-8 -*-

from traceback import print_exc

from pyload.plugins.Plugin import Base


class Expose(object):
    """ used for decoration to declare rpc services """

    def __new__(cls, f, *args, **kwargs):
        addonManager.addRPC(f.__module__, f.func_name, f.func_doc)
        return f


def threaded(f):

    def run(*args,**kwargs):
        addonManager.startThread(f, *args, **kwargs)
    return run


class Addon(Base):
    """
    Base class for addon plugins.
    """
    __name__ = "Addon"
    __type__ = "addon"
    __version__ = "0.2"

    __config__ = [("name", "type", "desc", "default")]

    __description__ = """Interface for addon"""
    __authors__ = [("mkaay", "mkaay@mkaay.de"),
                   ("RaNaN", "RaNaN@pyload.org")]


    #: automatically register event listeners for functions, attribute will be deleted dont use it yourself
    event_map = None

    # Alternative to event_map
    #: List of events the plugin can handle, name the functions exactly like eventname.
    event_list = None  # dont make duplicate entries in event_map

    #: periodic call interval in secondc
    interval = 60


    def __init__(self, core, manager):
        Base.__init__(self, core)

        #: Provide information in dict here, usable by API `getInfo`
        self.info = None

        #: Callback of periodical job task, used by AddonManager
        self.cb = None

        #: `AddonManager`
        self.manager = manager

        #register events
        if self.event_map:
            for event, funcs in self.event_map.iteritems():
                if type(funcs) in (list, tuple):
                    for f in funcs:
                        self.manager.addEvent(event, getattr(self,f))
                else:
                    self.manager.addEvent(event, getattr(self,funcs))

            #delete for various reasons
            self.event_map = None

        if self.event_list:
            for f in self.event_list:
                self.manager.addEvent(f, getattr(self,f))

            self.event_list = None

        self.setup()
        self.initPeriodical()


    def initPeriodical(self):
        if self.interval >=1:
            self.cb = self.core.scheduler.addJob(0, self._periodical, threaded=False)

    def _periodical(self):
        try:
            if self.isActivated(): self.periodical()
        except Exception, e:
            self.logError(_("Error executing addon: %s") % e)
            if self.core.debug:
                print_exc()

        self.cb = self.core.scheduler.addJob(self.interval, self._periodical, threaded=False)


    def __repr__(self):
        return "<Addon %s>" % self.__name__

    def setup(self):
        """ more init stuff if needed """
        pass

    def unload(self):
        """ called when addon was deactivated """
        pass

    def isActivated(self):
        """ checks if addon is activated"""
        return self.config.getPlugin(self.__name__, "activated")


    #event methods - overwrite these if needed
    def coreReady(self):
        pass

    def coreExiting(self):
        pass

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

    def newCaptchaTask(self, task):
        """ new captcha task for the plugin, it MUST set the handler and timeout or will be ignored """
        pass

    def captchaCorrect(self, task):
        pass

    def captchaInvalid(self, task):
        pass
