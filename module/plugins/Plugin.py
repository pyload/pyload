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

import os
from os import remove
from os import makedirs
from os import chmod
from os import stat
from os import name as os_name
from os.path import exists, join

if os.name != "nt":
    from os import chown
    from pwd import getpwnam
    from grp import getgrnam

from itertools import islice

from module.utils import save_join, decode, removeChars

def chunks(iterable, size):
    it = iter(iterable)
    item = list(islice(it, size))
    while item:
        yield item
        item = list(islice(it, size))


class Abort(Exception):
    """ raised when aborted """


class Fail(Exception):
    """ raised when failed """


class Reconnect(Exception):
    """ raised when reconnected """


class Retry(Exception):
    """ raised when start again from beginning """


class SkipDownload(Exception):
    """ raised when download should be skipped """


class Plugin(object):
    __name__ = "Plugin"
    __version__ = "0.4"
    __pattern__ = None
    __type__ = "hoster"
    __config__ = [("name", "type", "desc", "default")]
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

        self.ocr = None  # captcha reader instance
        self.account = pyfile.m.core.accountManager.getAccountPlugin(self.__name__) # account handler instance

        self.premium = False
        self.user = None

        if self.account and not self.account.canUse(): self.account = None
        if self.account:
            self.user, data = self.account.selectAccount()
            self.req = self.account.getAccountRequest(self.user)
            self.chunkLimit = -1 #enable chunks for all premium plugins
            self.resumeDownload = True #also enable resume (both will be ignored if server dont accept chunks)
            self.multiDL = True  #every hoster with account should provides multiple downloads
            self.premium = self.account.isPremium(self.user)  #premium status
        else:
            self.req = pyfile.m.core.requestFactory.getRequest(self.__name__)

        self.log = pyfile.m.core.log

        self.pyfile = pyfile
        self.thread = None # holds thread in future

        self.lastDownload = ""  # location where the last call to download was saved
        self.lastCheck = None  #re match of last checked matched
        self.js = self.core.js  # js engine
        self.cTask = None #captcha task

        self.html = None #some plugins store html code here

        self.init()

    def getChunkCount(self):
        if self.chunkLimit <= 0:
            return self.config["download"]["chunks"]
        return min(self.config["download"]["chunks"], self.chunkLimit)

    def __call__(self):
        return self.__name__

    def init(self):
        """ more init stuff if needed """
        pass

    def setup(self):
        """ setup for enviroment and other things, called before downloading (possibly more than one time)"""
        pass

    def preprocessing(self, thread):
        """ handles important things to do before starting """
        self.thread = thread

        if self.account:
            self.account.checkLogin(self.user)
        else:
            self.req.clearCookies()

        self.setup()

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

        return True, 10


    def setConf(self, option, value):
        """ sets a config value """
        self.config.setPlugin(self.__name__, option, value)

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

    def tempOffline(self):
        """ fail and indicates file ist temporary offline, the core may take consequences """
        raise Fail("temp. offline")

    def retry(self):
        """ begin again from the beginning """
        raise Retry

    def invalidCaptcha(self):
        if self.cTask:
            self.cTask.invalid()

    def correctCaptcha(self):
        if self.cTask:
            self.cTask.correct()

    def decryptCaptcha(self, url, get={}, post={}, cookies=False, forceUser=False, imgtype='jpg', result_type='textual'):
        """ loads the catpcha and decrypt it or ask the user for input """
        
        img = self.load(url, get=get, post=post, cookies=cookies)

        id = ("%.2f" % time())[-6:].replace(".","")
        temp_file = open(join("tmp", "tmpCaptcha_%s_%s.%s" % (self.__name__, id, imgtype)), "wb") 
        temp_file.write(img)
        temp_file.close()

        has_plugin = self.core.pluginManager.captchaPlugins.has_key(self.__name__)
        
        if self.core.captcha:
            Ocr = self.core.pluginManager.getCaptchaPlugin(self.__name__)
        else:
            Ocr = None

        if Ocr and not forceUser:
            sleep(randint(3000, 5000) / 1000.0)
            if self.pyfile.abort: raise Abort
            
            ocr = Ocr()
            result = ocr.get_captcha(temp_file.name)
        else:
            
            captchaManager = self.core.captchaManager
            task = captchaManager.newTask(img, imgtype, temp_file.name, result_type)
            self.cTask = task
            captchaManager.handleCaptcha(task)
            
            while task.isWaiting():
                if self.pyfile.abort:
                    captchaManager.removeTask(task)
                    raise Abort
                sleep(1)

            captchaManager.removeTask(task)

            if task.error and has_plugin: #ignore default error message since the user could use OCR
                self.fail(_("Pil and tesseract not installed and no Client connected for captcha decrypting"))
            elif task.error:
                self.fail(task.error)
            elif not task.result:
                self.fail(_("No captcha result obtained in appropiate time by any of the plugins."))


            result = task.result
            self.log.debug("Received captcha result: %s" % str(result))

        if not self.core.debug:
          try:
            remove(temp_file.name)
          except:
            pass
        
        return result


    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, utf8=False):
        """ returns the content loaded """
        if self.pyfile.abort: raise Abort

        res = self.req.load(url, get, post, ref, cookies, just_header)

        if utf8:
            res = self.req.http.decodeResponse(res)
            #res = decode(res)

        if self.core.debug:
            from inspect import currentframe

            frame = currentframe()
            if not exists(join("tmp", self.__name__)):
                makedirs(join("tmp", self.__name__))

            f = open(
                join("tmp", self.__name__, "%s_line%s.dump.html" % (frame.f_back.f_code.co_name, frame.f_back.f_lineno))
                , "wb")
            del frame # delete the frame or it wont be cleaned

            try:
                tmp = res.encode("utf8")
            except:
                tmp = res

            f.write(tmp)
            f.close()

        if just_header:
            #parse header
            header = {"code": self.req.code}
            for line in res.splitlines():
                line = line.strip()
                if not line or ":" not in line: continue

                key, none, value = line.partition(":")
                key = key.lower().strip()
                value = value.strip()

                if header.has_key(key):
                    if type(header[key]) == list:
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value
            res = header

        return res

    def download(self, url, get={}, post={}, ref=True, cookies=True, disposition=False):
        """ downloads the url content to disk """

        self.checkForSameFiles()

        self.pyfile.setStatus("downloading")

        download_folder = self.config['general']['download_folder']

        location = save_join(download_folder, self.pyfile.package().folder)

        if not exists(location):
            makedirs(location, int(self.core.config["permission"]["folder"], 8))

            if self.core.config["permission"]["change_dl"] and os.name != "nt":
                try:
                    uid = getpwnam(self.config["permission"]["user"])[2]
                    gid = getgrnam(self.config["permission"]["group"])[2]

                    chown(location, uid, gid)
                except Exception, e:
                    self.log.warning(_("Setting User and Group failed: %s") % str(e))

        name = self.pyfile.name
        if os_name == 'nt':
            #delete illegal characters
            name = removeChars(name, '/\\?%*:|"<>')
        else:
            name = removeChars(name, '/\\"')

        filename = save_join(location, name)
        try:
            newname = self.req.httpDownload(url, filename, get=get, post=post, ref=ref, cookies=cookies,
                                            chunks=self.getChunkCount(), resume=self.resumeDownload,
                                            progressNotify=self.pyfile.progress.setValue, disposition=disposition)
        finally:
            self.pyfile.size = self.req.size

        if disposition and newname and newname != name: #triple check, just to be sure
            self.log.info("%(name)s saved as %(newname)s" % {"name": name, "newname": newname})
            self.pyfile.name = newname
            filename = save_join(location, newname)

        if self.core.config["permission"]["change_file"]:
            chmod(filename, int(self.core.config["permission"]["file"], 8))

        if self.core.config["permission"]["change_dl"] and os.name != "nt":
            try:
                uid = getpwnam(self.config["permission"]["user"])[2]
                gid = getgrnam(self.config["permission"]["group"])[2]

                chown(filename, uid, gid)
            except Exception, e:
                self.log.warning(_("Setting User and Group failed: %s") % str(e))

        self.lastDownload = filename
        return self.lastDownload

    def checkDownload(self, rules, api_size=0, max_size=50000, delete=True, read_size=0):
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
        #produces encoding errors, better log to other file in the future?
        #self.log.debug("Content: %s" % content)
        for name, rule in rules.iteritems():
            if type(rule) in (str, unicode):
                if rule in content:
                    if delete:
                        remove(self.lastDownload)
                    return name
            elif hasattr(rule, "search"):
                m = rule.search(content)
                if m:
                    if delete:
                        remove(self.lastDownload)
                    self.lastCheck = m
                    return name


    def getPassword(self):
        password = self.pyfile.package().password
        if not password: return ""
        return password


    def checkForSameFiles(self, starting=False):
        """ checks if same file was/is downloaded within same package and raise exception """

        pack = self.pyfile.package()

        cache = self.core.files.cache.values()

        for pyfile in cache:
            if pyfile != self.pyfile and pyfile.name == self.pyfile.name and pyfile.package().folder == pack.folder:
                if pyfile.status in (0, 12): #finished or downloading
                    raise SkipDownload(pyfile.pluginname)
                elif pyfile.status in (5, 7) and starting: #a download is waiting and was appenrently started before
                    raise SkipDownload(pyfile.pluginname)

        #TODO check same packagenames
        pyfile = self.core.db.findDuplicates(self.pyfile.id, self.pyfile.packageid, self.pyfile.name)
        if pyfile:
            download_folder = self.config['general']['download_folder']
            location = save_join(download_folder, pack.folder)
            if exists(save_join(location, self.pyfile.name)):
                raise SkipDownload(pyfile[0])

            self.log.debug("File %s not skipped, because it does not exists." % self.pyfile.name)

    def clean(self):
        """ clean everything and remove references """
        if hasattr(self, "pyfile"):
            del self.pyfile
        if hasattr(self, "req"):
            self.req.close()
            del self.req
        if hasattr(self, "thread"):
            del self.thread
        if hasattr(self, "html"):
            del self.html
