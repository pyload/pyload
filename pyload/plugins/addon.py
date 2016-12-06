# -*- coding: utf-8 -*-

#from functools import wraps
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str
from builtins import object
from pyload.utils import has_method, to_list

from .Base import Base


def class_name(p):
    return p.rpartition(".")[2]


def AddEventListener(event):
    """ Used to register method for events. Arguments needs to match parameter of event

    :param event: Name of event or list of them.
    """


    class _klass(object):
        def __new__(cls, f, *args, **kwargs):
            for ev in to_list(event):
                addonManager.addEventListener(class_name(f.__module__), f.__name__, ev)
            return f

    return _klass


def AddonHandler(label, desc, package=True, media=-1):
    """ Register Handler for files, packages, or arbitrary callable methods. In case package is True (default)
        The method should only accept a pid as argument. When media is set it will work on files
        and should accept a fileid. Only when both is None the method can be arbitrary.

    :param label: verbose name
    :param desc: short description
    :param package: True if method works withs packages
    :param media: media type of the file to work with.
    """


    class _klass(object):
        def __new__(cls, f, *args, **kwargs):
            addonManager.addAddonHandler(class_name(f.__module__), f.__name__, label, desc,
                                         f.__code__.co_varnames[1:], package, media)
            return f

    return _klass


def AddonProperty(name, desc, default=None, fire_event=True):
    """ Use this function to declare class variables, that will be exposed as :class:`AddonInfo`.
        It works similar to the @property function. You declare the variable like `state = AddonProperty(...)`
        and use it as any other variable.

    :param name: display name
    :param desc: verbose description
    :param default: the default value
    :param fire_event: Fire `addon:property:change` event, when modified
    """

    # generated name for the attribute
    h = "__Property" + str(hash(name) ^ hash(desc))

    addonManager.addInfoProperty(h, name, desc)

    def _get(self):
        if not hasattr(self, h):
            return default

        return getattr(self, h)

    def _set(self, value):
        if fire_event:
            self.manager.dispatchEvent("addon:property:change", value)

        return setattr(self, h, value)

    def _del(self):
        return delattr(self, h)

    return property(_get, _set, _del)


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

    #: periodic call interval in seconds
    interval = 0

    __type__ = "addon"

    def __init__(self, core, manager, user=None):
        Base.__init__(self, core, user)

        #: Callback of periodical job task, used by addonManager
        self.cb = None

        #: `AddonManager`
        self.manager = manager

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
        except Exception as e:
            self.core.log.error(_("Error executing addon: %s") % str(e))
            self.core.print_exc()

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
