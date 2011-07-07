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
    
    @author: mkaay
    @interface-version: 0.2
"""

from thread import start_new_thread


class Expose(object):
    """ used for decoration to declare rpc services """
    def __init__(self, *args, **kwargs):
        self._f = args[0]
        hookManager.addRPC(self._f.__module__, self._f.func_name, self._f.func_doc)

    def __get__(self, obj, klass):
        self._obj = obj
        return self

    def __call__(self, *args, **kwargs):
        return self._f(self._obj, *args, **kwargs)

def threaded(f):
    def run(*args,**kwargs):
        return start_new_thread(f, args, kwargs)
    return run

class Hook():
    """
    Base class for hook plugins.
    """
    __name__ = "Hook"
    __version__ = "0.2"
    __type__ = "hook"
    __threaded__ = []
    __config__ = [ ("name", "type", "desc" , "default") ]
    __description__ = """interface for hook"""
    __author_name__ = ("mkaay", "RaNaN")
    __author_mail__ = ("mkaay@mkaay.de", "RaNaN@pyload.org")

    #: automatically register event listeners for functions, attribute will be deleted dont use it yourself
    event_map = None

    #: periodic call interval in secondc
    interval = 60

    def __init__(self, core, manager):
        self.core = core 
        self.log = core.log
        self.config = core.config

        #: Provide information in dict here, usable by API `getInfo`
        self.info = None

        #: `HookManager`
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

        self.setup()

    def __repr__(self):
        return "<Hook %s>" % self.__name__
               
    def setup(self):
        """ more init stuff if needed"""
        pass
    
    def isActivated(self):
        """ checks if hook is activated"""
        return self.config.getPlugin(self.__name__, "activated")
    
    def getConfig(self, option):
        """ gets config values """
        return self.config.getPlugin(self.__name__, option)
        
    def setConfig(self, option, value):
        """ sets config value """
        self.config.setPlugin(self.__name__, option, value)

    #log functions
    def logInfo(self, msg):
        self.log.info("%s: %s" % (self.__name__, msg))
    def logWarning(self, msg):
        self.log.warning("%s: %s" % (self.__name__, msg))
    def logError(self, msg):
        self.log.error("%s: %s" % (self.__name__, msg))
    def logDebug(self, msg):
        self.log.debug("%s: %s" % (self.__name__, msg))

    #event methods - overwrite these if needed    
    def coreReady(self):
        pass
    
    def downloadStarts(self, pyfile):
        pass
    
    def downloadFinished(self, pyfile):
        pass
    
    def downloadFailed(self, pyfile):
        pass
    
    def packageFinished(self, pypack):
        pass
    
    def packageFailed(self, pypack):
        pass
    
    def beforeReconnecting(self, ip):
        pass
    
    def afterReconnecting(self, ip):
        pass
    
    def periodical(self):
        pass

    def unrarFinished(self, folder, fname):
        pass

    def newCaptchaTask(self, task):
        """ new captcha task for the plugin, it MUST set the handler and timeout or will be ignored """
        pass

    def captchaCorrect(self, task):
        pass

    def captchaInvalid(self, task):
        pass