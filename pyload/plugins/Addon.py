# -*- coding: utf-8 -*-

from traceback import print_exc

#from functools import wraps
from pyload.utils import has_method, to_list

from Base import Base


def class_name(p):
    return p.rpartition(".")[2]


def AddEventListener(event):
    """ Used to register method for events. Arguments needs to match parameter of event

    :param event: Name of event or list of them.
    """

    class _klass(object):
        def __new__(cls, f, *args, **kwargs):
            for ev in to_list(event):
                addonManager.addEventListener(class_name(f.__module__), f.func_name, ev)
            return f

    return _klass


def AddonHandler(desc, media=None):
    """ Register Handler for files, packages, or arbitrary callable methods.
        To let the method work on packages/files, media must be set and the argument named pid or fid.

    :param desc: verbose description
    :param media: if True or bits of media type
    """
    pass


def AddonInfo(desc):
    """ Called to retrieve information about the current state.
    Decorated method must return anything convertable into string.

    :param desc: verbose description
    """
    pass


def threaded(f):
    """ Decorator to run method in a thread. """

    #@wraps(f)
    def run(*args, **kwargs):
        addonManager.startThread(f, *args, **kwargs)

    return run


class Addon(Base):
    """
    Base class for addon plugins. Use @threaded decorator for all longer running tasks.

    Decorate methods with @Expose, @AddEventListener, @ConfigHandler

    """

    #: automatically register event listeners for functions, attribute will be deleted don't use it yourself
    event_map = None

    #: periodic call interval in seconds
    interval = 0

    def __init__(self, core, manager, user=None):
        Base.__init__(self, core, user)

        #: Provide information in dict here, usable by API `getInfo`
        self.info = None

        #: Callback of periodical job task, used by addonManager
        self.cb = None

        #: `AddonManager`
        self.manager = manager

        #register events
        if self.event_map:
            for event, funcs in self.event_map.iteritems():
                if type(funcs) in (list, tuple):
                    for f in funcs:
                        self.evm.listenTo(event, getattr(self, f))
                else:
                    self.evm.listenTo(event, getattr(self, funcs))

            #delete for various reasons
            self.event_map = None

        self.init()

        # start periodically if set
        self.startPeriodical(self.interval, 0)

    def startPeriodical(self, interval, wait):
        """ Starts the periodical calls with given interval. Older entries will be canceled.
        :param interval: interval in seconds
        :param wait: time to wait in seconds before periodically starts
        :return: True if s
        """
        if interval < 1:
            return False

        # stop running callback
        if self.cb:
            self.stopPeriodical()

        self.cb = self.core.scheduler.addJob(wait, self._periodical, threaded=False)
        self.interval = interval
        return True

    def stopPeriodical(self):
        """ Stops periodical call if existing
        :return: True if the callback was stopped, false otherwise.
        """
        if self.cb and self.core.scheduler.removeJob(self.cb):
            self.cb = None
            return True
        else:
            return False

    def _periodical(self):
        try:
            if self.isActivated(): self.periodical()
        except Exception, e:
            self.core.log.error(_("Error executing addons: %s") % str(e))
            if self.core.debug:
                print_exc()

        if self.cb:
            self.cb = self.core.scheduler.addJob(self.interval, self._periodical, threaded=False)

    def __repr__(self):
        return "<Addon %s>" % self.__name__

    def isActivated(self):
        """ checks if addon is activated"""
        return True if self.__internal__ else self.getConfig("activated")

    def getCategory(self):
        return self.core.pluginManager.getCategory(self.__name__)

    def init(self):
        pass

    def activate(self):
        """  Used to activate the addon """
        if has_method(self.__class__, "coreReady"):
            self.logDebug("Deprecated method .coreReady() use activate() instead")
            self.coreReady()

    def deactivate(self):
        """ Used to deactivate the addon. """
        pass

    def periodical(self):
        pass

    def newInteractionTask(self, task):
        """ new interaction task for the plugin, it MUST set the handler and timeout or will be ignored """
        pass

    def taskCorrect(self, task):
        pass

    def taskInvalid(self, task):
        pass

    # public events starts from here
    def downloadPreparing(self, pyfile):
        pass

    def downloadFinished(self, pyfile):
        pass

    def downloadFailed(self, pyfile):
        pass

    def packageFinished(self, pypack):
        pass