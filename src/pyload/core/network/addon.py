# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import ADDONMANAGER, object, str

from future import standard_library

from pyload.utils.check import hasmethod
from pyload.utils.convert import to_list

from .base import Base

standard_library.install_aliases()


def class_name(path):
    return path.rpartition(".")[2]


def add_event_listener(event):
    """
    Used to register method for events.
    Arguments needs to match parameter of event.

    :param event: Name of event or list of them.
    """
    class klass(object):
        def __new__(cls, func, *args, **kwargs):
            for ev in to_list(event, []):
                ADDONMANAGER.add_event_listener(
                    class_name(func.__module__), func.__name__, ev)
            return func
    return klass


def addon_handler(label, desc, package=True, media=-1):
    """
    Register Handler for files, packages, or arbitrary callable methods. In case package is True (default).
    The method should only accept a pid as argument. When media is set it will work on files
    and should accept a fileid. Only when both is None the method can be arbitrary.

    :param label: verbose name
    :param desc: short description
    :param package: True if method works withs packages
    :param media: media type of the file to work with.
    """
    class klass(object):
        def __new__(cls, func, *args, **kwargs):
            ADDONMANAGER.add_addon_handler(
                class_name(func.__module__), func.__name__, label, desc,
                func.__code__.co_varnames[1:], package, media)
            return func
    return klass


def addon_property(name, desc, default=None, fire_event=True):
    """
    Use this function to declare class variables, that will be exposed as :class:`AddonInfo`.
    It works similar to the @property function. You declare the variable like `state = addon_property(...)`
    and use it as any other variable.

    :param name: display name
    :param desc: verbose description
    :param default: the default value
    :param fire_event: Fire `addon:property:change` event, when modified
    """
    # generated name for the attribute
    h = "__Property{0}".format(hash(name) ^ hash(desc))

    ADDONMANAGER.add_info_property(h, name, desc)

    def _get(self):
        if not hasattr(self, h):
            return default

        return getattr(self, h)

    def _set(self, value):
        if fire_event:
            self.__manager.fire("addon:property:change", value)

        return setattr(self, h, value)

    def _del(self):
        return delattr(self, h)

    return property(_get, _set, _del)


def threaded(f):
    """
    Decorator to run method in a thread.
    """
    def run(*args, **kwargs):
        ADDONMANAGER.start_thread(f, *args, **kwargs)
    return run


class Addon(Base):
    """
    Base class for addon plugins. Use @threaded decorator for all longer running tasks.

    Decorate methods with @Expose, @add_event_listener, @ConfigHandler

    """
    # periodic call interval in seconds
    interval = 0

    __type__ = "addon"

    def __init__(self, core, manager, user=None):
        Base.__init__(self, core, user)

        # Callback of periodical job task, used by AddonManager
        self.cb = None

        # `AddonManager`
        self.__manager = manager

        self.init()

        # start periodically if set
        self.start_periodical(self.interval, 0)

    def start_periodical(self, interval, wait):
        """
        Starts the periodical calls with given interval. Older entries will be canceled.
        :param interval: interval in seconds
        :param wait: time to wait in seconds before periodically starts
        :return: True if s
        """
        if interval < 1:
            return False

        # stop running callback
        if self.cb:
            self.stop_periodical()

        self.cb = self.pyload_core.scheduler.enter(wait, 2, self._periodical)
        self.interval = interval
        return True

    def stop_periodical(self):
        """
        Stops periodical call if existing
        :return: True if the callback was stopped, false otherwise
        """
        if self.cb and self.pyload_core.scheduler.cancel(self.cb):
            self.cb = None
            return True
        else:
            return False

    def _periodical(self):
        try:
            if self.is_activated():
                self.periodical()
        except Exception as e:
            self.pyload_core.log.error(
                self._("Error executing addon: {0}").format(str(e)))
            # self.pyload_core.print_exc()

        if self.cb:
            self.cb = self.pyload_core.scheduler.enter(
                self.interval, 2, self._periodical)

    def __repr__(self):
        return "<Addon {0}>".format(self.__name__)

    def is_activated(self):
        """
        Checks if addon is activated.
        """
        return True if self.__internal__ else self.get_config("activated")

    def get_category(self):
        return self.pyload_core.pgm.get_category(self.__name__)

    def init(self):
        pass

    def activate(self):
        """
        Used to activate the addon.
        """
        if hasmethod(self.__class__, "core_ready"):
            self.log_debug(
                "Deprecated method .core_ready() use activate() instead")
            self.pyload_ready()

    def deactivate(self):
        """
        Used to deactivate the addon.
        """
        pass

    def periodical(self):
        pass

    def new_interaction_task(self, task):
        """
        New interaction task for the plugin, it MUST set the handler and timeout or will be ignored.
        """
        pass

    def task_correct(self, task):
        pass

    def task_invalid(self, task):
        pass

    # public events starts from here
    def download_preparing(self, file):
        pass

    def download_finished(self, file):
        pass

    def download_failed(self, file):
        pass

    def package_finished(self, pack):
        pass
