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

    @author: RaNaN, spoob, mkaay
"""

from time import time
from time import sleep

from random import randint

import sys

import os
from os import remove
from os import makedirs
from os import chmod
from os import stat
from os.path import exists
from os.path import join
from os.path import basename

if os.name != "nt":
    from os import chown
    from pwd import getpwnam
    from grp import getgrnam

from mimetypes import guess_type

from itertools import islice

from module.network.helper import waitFor

def chunks(iterable, size):
  it = iter(iterable)
  item = list(islice(it, size))
  while item:
    yield item
    item = list(islice(it, size))

def dec(func):
    def new(*args):
        if args[0].pyfile.abort:
            raise Abort
        return func(*args)
    return new

class Abort(Exception):
    """ raised when aborted """

class Fail(Exception):
    """ raised when failed """

class Reconnect(Exception):
    """ raised when reconnected """

class Retry(Exception):
    """ raised when start again from beginning """

class Plugin(object):
    __name__ = "Plugin"
    __version__ = "0.4"
    __pattern__ = None
    __type__ = "hoster"
    __config__ = [ ("name", "type", "desc" , "default") ]
    __description__ = """Base Plugin"""
    __author_name__ = ("RaNaN", "spoob", "mkaay")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org", "mkaay@mkaay.de")


    def __init__(self, pyfile):
        self.config = pyfile.m.core.config
        self.core = pyfile.m.core

        self.wantReconnect = False
        self.multiDL = True
        self.limitDL = 0
        self.chunkLimit = 1
        self.resumeDownload = False

        self.waitUntil = 0 # time() + wait in seconds
        self.waiting = False
        
        self.premium = False

        self.ocr = None  # captcha reader instance
        self.account = pyfile.m.core.accountManager.getAccountPlugin(self.__name__) # account handler instance
        if self.account and not self.account.canUse(): self.account = None
        if self.account:
            self.user, data = self.account.selectAccount()
            self.req = self.account.getAccountRequest(self.user)
            #self.req.canContinue = True
        else:
            self.req = pyfile.m.core.requestFactory.getRequest(self.__name__)
        self.req.progressNotify = pyfile.progress.setValue
        
        self.log = pyfile.m.core.log

        self.pyfile = pyfile
        self.thread = None # holds thread in future

        self.lastDownload = ""  # location where the last call to download was saved
        self.lastCheck = None  #re match of last checked matched
        self.js = self.core.js  # js engine

        #self.setup()
    
    def getChunkCount(self):
        if self.chunkLimit <= 0:
            return self.config["general"]["chunks"]
        return min(self.config["general"]["chunks"], self.chunkLimit)
    
    def __call__(self):
        return self.__name__

    def __del__(self):
        if hasattr(self, "pyfile"):
            del self.pyfile
        if hasattr(self, "req"):
            del self.req

    def setup(self):
        """ more init stuff if needed """
        pass

    def preprocessing(self, thread):
        """ handles important things to do before starting """
        self.setup()
        self.thread = thread

        if self.account:
            self.multiDL = True  #every hoster with account should provides multiple downloads
        else:
            self.req.clearCookies()

        if self.core.config["proxy"]["activated"]:
            self.req.add_proxy(None, self.core.config["proxy"]["address"])

        self.pyfile.setStatus("starting")

        return self.process(self.pyfile)

    #----------------------------------------------------------------------
    def process(self, pyfile):
        """the 'main' method of every plugin"""
        raise NotImplementedError
    
    def resetAccount(self):
        """ dont use account and retry download """
        self.account = None
        self.req = self.core.requestFactory.getRequest(self.__name__)
        self.retry()
    
    def checksum(self, local_file=None):
        """
        return codes:
        0  - checksum ok
        1  - checksum wrong
        5  - can't get checksum
        10 - not implemented
        20 - unknown error
        """
        #@TODO checksum check hook

        return (True, 10)


    def setConf(self, option, value):
        """ sets a config value """
        self.config.setPlugin(self.__name__, option, value)

    def removeConf(self, option):
        """ removes a config value """
        raise NotImplementedError

    def getConf(self, option):
        """ gets a config value """
        return self.config.getPlugin(self.__name__, option)

    def setConfig(self, option, value):
      """ sets a config value """
      self.setConf(option, value)
      
    def getConfig(self, option):
      """ gets a config value """
      return self.getConf(option)
      
      
    def setWait(self, seconds, reconnect=False):
        """ set the wait time to specified seconds """
        if reconnect:
            self.wantReconnect = True
        self.pyfile.waitUntil = time() + int(seconds)

    def wait(self):
        """ waits the time previously set """
        self.waiting = True
        self.pyfile.setStatus("waiting")
        
        while self.pyfile.waitUntil > time():
            self.thread.m.reconnecting.wait(2)
            
            if self.pyfile.abort: raise Abort
            if self.thread.m.reconnecting.isSet():
                self.waiting = False
                self.wantReconnect = False
                raise Reconnect
        
        self.waiting = False
        self.pyfile.setStatus("starting")

    def fail(self, reason):
        """ fail and give reason """
        raise Fail(reason)

    def offline(self):
        """ fail and indicate file is offline """
        raise Fail("offline")

    def retry(self):
        """ begin again from the beginning """
        raise Retry

    def decryptCaptcha(self, url, get={}, post={}, cookies=False, forceUser=False):
        """ loads the catpcha and decrypt it or ask the user for input """
        
        content = self.load(url, get=get, post=post, cookies=cookies)

        id = ("%.2f" % time())[-6:]
        temp = open(join("tmp","tmpCaptcha_%s_%s" % (id, self.__name__)), "wb")
        
        temp.write(content)
        temp.close()

        has_plugin = self.core.pluginManager.captchaPlugins.has_key(self.__name__)
        
        if self.core.captcha:
            Ocr = self.core.pluginManager.getCaptchaPlugin(self.__name__)
        else:
            Ocr = None

        if Ocr and not forceUser:
            sleep(randint(3000, 5000) / 1000.0)
            if self.pyfile.abort: raise Abort
            
            ocr = Ocr()
            result = ocr.get_captcha(temp.name)
        else:
            captchaManager = self.core.captchaManager
            mime = guess_type(temp.name)
            task = captchaManager.newTask(self)
            task.setCaptcha(content, mime[0])
            task.setWaiting()
            while not task.getStatus() == "done":
                if not self.core.isClientConnected():
                    task.removeTask()
                    #temp.unlink(temp.name)
                    if has_plugin:
                        self.fail(_("Pil and tesseract not installed and no Client connected for captcha decrypting"))
                    else:
                        self.fail(_("No Client connected for captcha decrypting"))
                if self.pyfile.abort:
                    task.removeTask()
                    raise Abort
                sleep(1)
            result = task.getResult()
            task.removeTask()

        if not self.core.debug:
          try:
            remove(temp.name)
          except:
            pass
        
        return result


    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, no_post_encode=False, raw_cookies={}):
        """ returns the content loaded """
        if self.pyfile.abort: raise Abort

        res = self.req.getPage(url, get=get, post=post, cookies=cookies)
        if self.core.debug:
            from inspect import currentframe
            frame = currentframe()
            if not exists(join("tmp", self.__name__)):
                makedirs(join("tmp", self.__name__))

            f = open(join("tmp", self.__name__, "%s_line%s.dump.html" % (frame.f_back.f_code.co_name, frame.f_back.f_lineno)), "wb")
            f.write(res.encode("utf8"))
            f.close()
            
        return res

    def download(self, url, get={}, post={}, ref=True, cookies=True):
        """ downloads the url content to disk """

        self.pyfile.setStatus("downloading")

        self.pyfile.size = 0

        download_folder = self.config['general']['download_folder'].decode("utf8")
        
        location = join(download_folder.encode(sys.getfilesystemencoding(), "replace"), self.pyfile.package().folder.replace(":", "").encode(sys.getfilesystemencoding(), "replace")) # remove : for win compability

        if not exists(location):
            makedirs(location, int(self.core.config["permission"]["folder"],8))

            if self.core.config["permission"]["change_dl"] and os.name != "nt":
                try:
                    uid = getpwnam(self.config["permission"]["user"])[2]
                    gid = getgrnam(self.config["permission"]["group"])[2]

                    chown(location, uid, gid)
                except Exception,e:
                    self.log.warning(_("Setting User and Group failed: %s") % str(e))

        name = self.pyfile.name.encode(sys.getfilesystemencoding(), "replace")
        filename = join(location, name)
        d = self.req.httpDownload(url, filename, get=get, post=post, chunks=self.getChunkCount(), resume=self.resumeDownload)
        self.pyfile.download = d
        d.addProgress("percent", self.pyfile.progress.setValue)
        waitFor(d)

        if d.abort: raise Abort

        self.pyfile.download = None
        newname = basename(filename)

        self.pyfile.size = d.size

        if newname and newname != name:
            self.log.info("%(name)s saved as %(newname)s" % {"name": name, "newname": newname})
            name = newname
            #self.pyfile.name = newname

        if self.core.config["permission"]["change_file"]:
            chmod(join(location, name), int(self.core.config["permission"]["file"],8))

        if self.core.config["permission"]["change_dl"] and os.name != "nt":
            try:
                uid = getpwnam(self.config["permission"]["user"])[2]
                gid = getgrnam(self.config["permission"]["group"])[2]

                chown(join(location, name), uid, gid)
            except Exception,e:
                self.log.warning(_("Setting User and Group failed: %s") % str(e))

        self.lastDownload = join(location, name)
        return self.lastDownload

    def checkDownload(self, rules, api_size=0 ,max_size=50000, delete=True, read_size=0):
        """ checks the content of the last downloaded file
        rules - dict with names and rules to match(re or strings)
        size - excpected size
        @return name of first rule matched or None"""

        if not exists(self.lastDownload): return None
        
        size = stat(self.lastDownload)
        size = size.st_size

        if api_size and api_size <= size: return None
        elif size > max_size and not read_size: return None
        self.log.debug("Download Check triggered")
        f = open(self.lastDownload, "rb")
        content = f.read(read_size if read_size else -1)
        f.close()
        self.log.debug("Content: %s" % content)
        for name, rule in rules.iteritems():
            if type(rule) in (str, unicode):
                if rule in content:
                    if delete:
                        remove(self.lastDownload)
                    return name
            elif hasattr(rule, "match"):
                m = rule.match(content)
                if m:
                    if delete:
                        remove(self.lastDownload)
                    self.lastCheck = m
                    return name
