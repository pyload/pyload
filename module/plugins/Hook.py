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

def threaded(f):
    def run(*args,**kwargs):
        return start_new_thread(f, args, kwargs)
    return run

class Hook():
    __name__ = "Hook"
    __version__ = "0.2"
    __type__ = "hook"
    __threaded__ = []
    __config__ = [ ("name", "type", "desc" , "default") ]
    __description__ = """interface for hook"""
    __author_name__ = ("mkaay", "RaNaN")
    __author_mail__ = ("mkaay@mkaay.de", "RaNaN@pyload.org")
    
    def __init__(self, core):
        self.core = core 
        self.log = core.log
        self.config = core.config
        
        self.interval = 60
        
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

    def captchaWrong(self, task):
        pass