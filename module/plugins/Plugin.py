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

from time import time, sleep
from random import randint

import os
from os import remove, makedirs, chmod, stat
from os.path import exists, join

if os.name != "nt":
    from os import chown
    from pwd import getpwnam
    from grp import getgrnam

from itertools import islice

from module.utils import save_join, save_path, fs_encode, fs_decode

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


class Base(object):
    """
    A Base class with log/config/db methods *all* plugin types can use
    """

    def __init__(self, core):
        #: Core instance
        self.core = core
        #: logging instance
        self.log = core.log
        #: core config
        self.config = core.config

    #log functions
    def logInfo(self, *args):
        self.log.info("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))

    def logWarning(self, *args):
        self.log.warning("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))

    def logError(self, *args):
        self.log.error("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))

    def logDebug(self, *args):
        self.log.debug("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))


    def setConf(self, option, value):
        """ see `setConfig` """
        self.core.config.setPlugin(self.__name__, option, value)

    def setConfig(self, option, value):
        """ Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.setConf(option, value)

    def getConf(self, option):
        """ see `getConfig` """
        return self.core.config.getPlugin(self.__name__, option)

    def getConfig(self, option):
        """ Returns config value for current plugin

        :param option:
        :return:
        """
        return self.getConf(option)

    def setStorage(self, key, value):
        """ Saves a value persistently to the database """
        self.core.db.setStorage(self.__name__, key, value)

    def store(self, key, value):
        """ same as `setStorage` """
        self.core.db.setStorage(self.__name__, key, value)

    def getStorage(self, key=None, default=None):
        """ Retrieves saved value or dict of all saved entries if key is None """
        if key is not None:
            return self.core.db.getStorage(self.__name__, key) or default
        return self.core.db.getStorage(self.__name__, key)

    def retrieve(self, *args, **kwargs):
        """ same as `getStorage` """
        return self.getStorage(*args, **kwargs)

    def delStorage(self, key):
        """ Delete entry in db """
        self.core.db.delStorage(self.__name__, key)


class Plugin(Base):
    """
    Base plugin for hoster/crypter.
    Overwrite `process` / `decrypt` in your subclassed plugin.
    """
    __name__ = "Plugin"
    __version__ = "0.4"
    __pattern__ = None
    __type__ = "hoster"
    __config__ = [("name", "type", "desc", "default")]
    __description__ = """Base Plugin"""
    __author_name__ = ("RaNaN", "spoob", "mkaay")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org", "mkaay@mkaay.de")

    def __init__(self, pyfile):
        Base.__init__(self, pyfile.m.core)

        self.wantReconnect = False
        #: enables simultaneous processing of multiple downloads
        self.multiDL = True
        self.limitDL = 0
        #: chunk limit
        self.chunkLimit = 1
        self.resumeDownload = False

        #: time() + wait in seconds
        self.waitUntil = 0
        self.waiting = False

        self.ocr = None  #captcha reader instance
        #: account handler instance, see :py:class:`Account`
        self.account = pyfile.m.core.accountManager.getAccountPlugin(self.__name__)

        #: premium status
        self.premium = False
        #: username/login
        self.user = None

        if self.account and not self.account.canUse(): self.account = None
        if self.account:
            self.user, data = self.account.selectAccount()
            #: Browser instance, see `network.Browser`
            self.req = self.account.getAccountRequest(self.user)
            self.chunkLimit = -1 # chunk limit, -1 for unlimited
            #: enables resume (will be ignored if server dont accept chunks)
            self.resumeDownload = True
            self.multiDL = True  #every hoster with account should provide multiple downloads
            #: premium status
            self.premium = self.account.isPremium(self.user)
        else:
            self.req = pyfile.m.core.requestFactory.getRequest(self.__name__)

        #: associated pyfile instance, see `PyFile`
        self.pyfile = pyfile
        self.thread = None # holds thread in future

        #: location where the last call to download was saved
        self.lastDownload = ""
        #: re match of the last call to `checkDownload`
        self.lastCheck = None
        #: js engine, see `JsEngine`
        self.js = self.core.js
        self.cTask = None #captcha task

        self.retries = 0 # amount of retries already made
        self.html = None # some plugins store html code here

        self.init()

    def getChunkCount(self):
        if self.chunkLimit <= 0:
            return self.config["download"]["chunks"]
        return min(self.config["download"]["chunks"], self.chunkLimit)

    def __call__(self):
        return self.__name__

    def init(self):
        """initialize the plugin (in addition to `__init__`)"""
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


    def process(self, pyfile):
        """the 'main' method of every plugin, you **have to** overwrite it"""
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


    def setWait(self, seconds, reconnect=False):
        """Set a specific wait time later used with `wait`
        
        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
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

    def retry(self, max_tries=3, wait_time=1, reason=""):
        """Retries and begin again from the beginning

        :param max_tries: number of maximum retries
        :param wait_time: time to wait in seconds
        :param reason: reason for retrying, will be passed to fail if max_tries reached
        """
        if 0 < max_tries <= self.retries:
            if not reason: reason = "Max retries reached"
            raise Fail(reason)

        self.wantReconnect = False
        self.setWait(wait_time)
        self.wait()

        self.retries += 1
        raise Retry(reason)

    def invalidCaptcha(self):
        if self.cTask:
            self.cTask.invalid()

    def correctCaptcha(self):
        if self.cTask:
            self.cTask.correct()

    def decryptCaptcha(self, url, get={}, post={}, cookies=False, forceUser=False, imgtype='jpg',
                       result_type='textual'):
        """ Loads a captcha and decrypts it with ocr, plugin, user input

        :param url: url of captcha image
        :param get: get part for request
        :param post: post part for request
        :param cookies: True if cookies should be enabled
        :param forceUser: if True, ocr is not used
        :param imgtype: Type of the Image
        :param result_type: 'textual' if text is written on the captcha\
        or 'positional' for captcha where the user have to click\
        on a specific region on the captcha
        
        :return: result of decrypting
        """

        img = self.load(url, get=get, post=post, cookies=cookies)

        id = ("%.2f" % time())[-6:].replace(".", "")
        temp_file = open(join("tmp", "tmpCaptcha_%s_%s.%s" % (self.__name__, id, imgtype)), "wb")
        temp_file.write(img)
        temp_file.close()

        has_plugin = self.__name__ in self.core.pluginManager.captchaPlugins

        if self.core.captcha:
            Ocr = self.core.pluginManager.loadClass("captcha", self.__name__)
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


    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=False):
        """Load content at url and returns it

        :param url:
        :param get:
        :param post:
        :param ref:
        :param cookies:
        :param just_header: if True only the header will be retrieved and returned as dict
        :param decode: Wether to decode the output according to http header, should be True in most cases
        :return: Loaded content
        """
        if self.pyfile.abort: raise Abort
        #utf8 vs decode -> please use decode attribute in all future plugins
        if type(url) == unicode: url = str(url)

        res = self.req.load(url, get, post, ref, cookies, just_header, decode=decode)

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

                if key in header:
                    if type(header[key]) == list:
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value
            res = header

        return res

    def download(self, url, get={}, post={}, ref=True, cookies=True, disposition=False):
        """Downloads the content at url to download folder

        :param url:
        :param get:
        :param post:
        :param ref:
        :param cookies:
        :param disposition: if True and server provides content-disposition header\
        the filename will be changed if needed
        :return: The location where the file was saved
        """

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

        # convert back to unicode
        location = fs_decode(location)
        name = save_path(self.pyfile.name)

        filename = join(location, name)

        self.core.hookManager.dispatchEvent("downloadStarts", self.pyfile, url, filename)

        try:
            newname = self.req.httpDownload(url, filename, get=get, post=post, ref=ref, cookies=cookies,
                                            chunks=self.getChunkCount(), resume=self.resumeDownload,
                                            progressNotify=self.pyfile.setProgress, disposition=disposition)
        finally:
            self.pyfile.size = self.req.size

        if disposition and newname and newname != name: #triple check, just to be sure
            self.log.info("%(name)s saved as %(newname)s" % {"name": name, "newname": newname})
            self.pyfile.name = newname
            filename = join(location, newname)

        fs_filename = fs_encode(filename)

        if self.core.config["permission"]["change_file"]:
            chmod(fs_filename, int(self.core.config["permission"]["file"], 8))

        if self.core.config["permission"]["change_dl"] and os.name != "nt":
            try:
                uid = getpwnam(self.config["permission"]["user"])[2]
                gid = getgrnam(self.config["permission"]["group"])[2]

                chown(fs_filename, uid, gid)
            except Exception, e:
                self.log.warning(_("Setting User and Group failed: %s") % str(e))

        self.lastDownload = filename
        return self.lastDownload

    def checkDownload(self, rules, api_size=0, max_size=50000, delete=True, read_size=0):
        """ checks the content of the last downloaded file, re match is saved to `lastCheck`
        
        :param rules: dict with names and rules to match (compiled regexp or strings)
        :param api_size: expected file size
        :param max_size: if the file is larger then it wont be checked
        :param delete: delete if matched
        :param read_size: amount of bytes to read from files larger then max_size
        :return: dictionary key of the first rule that matched
        """
        lastDownload = fs_encode(self.lastDownload)
        if not exists(lastDownload): return None

        size = stat(lastDownload)
        size = size.st_size

        if api_size and api_size <= size: return None
        elif size > max_size and not read_size: return None
        self.log.debug("Download Check triggered")
        f = open(lastDownload, "rb")
        content = f.read(read_size if read_size else -1)
        f.close()
        #produces encoding errors, better log to other file in the future?
        #self.log.debug("Content: %s" % content)
        for name, rule in rules.iteritems():
            if type(rule) in (str, unicode):
                if rule in content:
                    if delete:
                        remove(lastDownload)
                    return name
            elif hasattr(rule, "search"):
                m = rule.search(content)
                if m:
                    if delete:
                        remove(lastDownload)
                    self.lastCheck = m
                    return name


    def getPassword(self):
        """ get the password the user provided in the package"""
        password = self.pyfile.package().password
        if not password: return ""
        return password


    def checkForSameFiles(self, starting=False):
        """ checks if same file was/is downloaded within same package

        :param starting: indicates that the current download is going to start
        :raises SkipDownload:
        """

        pack = self.pyfile.package()

        for pyfile in self.core.files.cache.values():
            if pyfile != self.pyfile and pyfile.name == self.pyfile.name and pyfile.package().folder == pack.folder:
                if pyfile.status in (0, 12): #finished or downloading
                    raise SkipDownload(pyfile.pluginname)
                elif pyfile.status in (
                5, 7) and starting: #a download is waiting/starting and was appenrently started before
                    raise SkipDownload(pyfile.pluginname)

        download_folder = self.config['general']['download_folder']
        location = save_join(download_folder, pack.folder, self.pyfile.name)

        if starting and self.core.config['download']['skip_existing'] and exists(location):
            size = os.stat(location).st_size
            if size >= self.pyfile.size:
                raise SkipDownload("File exists.")

        pyfile = self.core.db.findDuplicates(self.pyfile.id, self.pyfile.package().folder, self.pyfile.name)
        if pyfile:
            if exists(location):
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
