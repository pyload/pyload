# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
"""

from traceback import print_exc

#from functools import wraps
from module.utils import has_method, to_list

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

class ConfigHandler(object):
    """ Register method as config handler.

    Your method signature has to be:
        def foo(value=None):

    value will be passed to use your method to set the config.
    When value is None your method needs to return an interaction task for configuration.
    """

    def __new__(cls, f, *args, **kwargs):
        addonManager.addConfigHandler(class_name(f.__module__), f.func_name)
        return f

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
    def run(*args,**kwargs):
        addonManager.startThread(f, *args, **kwargs)
    return run

class Addon(Base):
    """
    Base class for addon plugins. Use @threaded decorator for all longer running tasks.

    Decorate methods with @Expose, @AddEventListener, @ConfigHandler

    """

    #: automatically register event listeners for functions, attribute will be deleted don't use it yourself
    event_map = None

    # Alternative to event_map
    #: List of events the plugin can handle, name the functions exactly like eventname.
    event_list = None  # dont make duplicate entries in event_map

    #: periodic call interval in seconds
    interval = 60

    def __init__(self, core, manager, user=None):
        Base.__init__(self, core, user)

        #: Provide information in dict here, usable by API `getInfo`
        self.info = None

        #: Callback of periodical job task, used by addonmanager
        self.cb = None

        #: `AddonManager`
        self.manager = manager

        #register events
        if self.event_map:
            for event, funcs in self.event_map.iteritems():
                if type(funcs) in (list, tuple):
                    for f in funcs:
                        self.evm.addEvent(event, getattr(self,f))
                else:
                    self.evm.addEvent(event, getattr(self,funcs))

            #delete for various reasons
            self.event_map = None

        if self.event_list:
            for f in self.event_list:
                self.evm.addEvent(f, getattr(self,f))

            self.event_list = None

        self.initPeriodical()
        self.init()
        self.setup()

    def initPeriodical(self):
        if self.interval >=1:
            self.cb = self.core.scheduler.addJob(0, self._periodical, threaded=False)

    def _periodical(self):
        try:
            if self.isActivated(): self.periodical()
        except Exception, e:
            self.core.log.error(_("Error executing addons: %s") % str(e))
            if self.core.debug:
                print_exc()

        self.cb = self.core.scheduler.addJob(self.interval, self._periodical, threaded=False)


    def __repr__(self):
        return "<Addon %s>" % self.__name__

    def isActivated(self):
        """ checks if addon is activated"""
        return True if self.__internal__ else self.getConfig("activated")

    def init(self):
        pass

    def setup(self):
        """ more init stuff if needed """
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

    def beforeReconnecting(self, ip):
        pass
    
    def afterReconnecting(self, ip):
        pass