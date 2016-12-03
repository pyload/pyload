# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
import os
from time import time

if os.name != "nt":
    from pyload.utils.fs import chown
    from pwd import getpwnam
    from grp import getgrnam

from pyload.utils import chunks as _chunks
from pyload.utils.fs import save_join, safe_filename, fs_encode, fs_decode, \
    remove, makedirs, chmod, stat, exists, join

from .Base import Base, Fail, Retry
from .network.DefaultRequest import DefaultRequest, DefaultDownload

# Import for Hoster Plugins
chunks = _chunks


class Reconnect(Exception):
    """ raised when reconnected """


class SkipDownload(Exception):
    """ raised when download should be skipped """


class Hoster(Base):
    """
    Base plugin for hoster plugin. Overwrite getInfo for online status retrieval, process for downloading.
    """

    #: Class used to make requests with `self.load`
    REQUEST_CLASS = DefaultRequest

    #: Class used to make download
    DOWNLOAD_CLASS = DefaultDownload

    @staticmethod
    def getInfo(urls):
        """This method is used to retrieve the online status of files for hoster plugins.

        :param urls: List of urls
        :return: yield list of :class:`LinkStatus` as result
        """
        pass

    __type__ = "hoster"

    def __init__(self, pyfile):
        # TODO: pyfile.owner, but it's not correct yet
        Base.__init__(self, pyfile.m.core)

        self.wantReconnect = False
        #: enables simultaneous processing of multiple downloads
        self.limitDL = 0
        #: chunk limit
        self.chunkLimit = 1
        #: enables resume (will be ignored if server dont accept chunks)
        self.resumeDownload = False

        #: plugin is waiting
        self.waiting = False

        self.ocr = None  #captcha reader instance
        #: account handler instance, see :py:class:`Account`
        self.account = self.core.accountManager.selectAccount(self.__name__, self.owner)

        #: premium status
        self.premium = False

        if self.account:
            #: Request instance bound to account
            self.req = self.account.getAccountRequest()
            # Default:  -1, True, True
            self.chunkLimit, self.limitDL, self.resumeDownload = self.account.getDownloadSettings()
            self.premium = self.account.isPremium()
        else:
            self.req = self.core.requestFactory.getRequest(klass=self.REQUEST_CLASS)

        #: Will hold the download class
        self.dl = None

        #: associated pyfile instance, see `PyFile`
        self.pyfile = pyfile
        self.thread = None # holds thread in future

        #: location where the last call to download was saved
        self.lastDownload = ""
        #: re match of the last call to `checkDownload`
        self.lastCheck = None

        self.retries = 0 # amount of retries already made
        self.html = None # some plugins store html code here

        self.init()

    @property
    def user(self):
        self.logDebug("Deprecated usage of self.user -> use self.account.loginname")
        if self.account:
            return self.account.loginname

    def getMultiDL(self):
        return self.limitDL <= 0

    def setMultiDL(self, val):
        self.limitDL = 0 if val else 1

    #: virtual attribute using self.limitDL on behind
    multiDL = property(getMultiDL, setMultiDL)

    def getChunkCount(self):
        if self.chunkLimit <= 0:
            return self.config["download"]["chunks"]
        return min(self.config["download"]["chunks"], self.chunkLimit)

    def getDownloadLimit(self):
        if self.account:
            limit = self.account.options.get("limitDL", 0)
            if limit == "": limit = 0
            if self.limitDL > 0: # a limit is already set, we use the minimum
                return min(int(limit), self.limitDL)
            else:
                return int(limit)
        else:
            return self.limitDL


    def __call__(self):
        return self.__name__

    def init(self):
        """initialize the plugin (in addition to `__init__`)"""
        pass

    def setup(self):
        """ setup for environment and other things, called before downloading (possibly more than one time)"""
        pass

    def preprocessing(self, thread):
        """ handles important things to do before starting """
        self.thread = thread

        if self.account:
            # will force a re-login or reload of account info if necessary
            self.account.getAccountInfo()
        else:
            self.req.reset()

        self.setup()

        self.pyfile.setStatus("starting")

        return self.process(self.pyfile)

    def process(self, pyfile):
        """the 'main' method of every plugin, you **have to** overwrite it"""
        raise NotImplementedError

    def abort(self):
        return self.pyfile.abort

    def resetAccount(self):
        """ don't use account and retry download """
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
        #@TODO checksum check addon

        return True, 10

    def setWait(self, seconds, reconnect=None):
        """Set a specific wait time later used with `wait`

        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
        if reconnect is not None:
            self.wantReconnect = reconnect
        self.pyfile.waitUntil = time() + int(seconds)

    def wait(self, seconds=None, reconnect=None):
        """ Waits the time previously set or use these from arguments. See `setWait`
        """
        if seconds is not None:
            self.setWait(seconds, reconnect)

        self._wait()

    def _wait(self):
        self.waiting = True
        self.pyfile.setStatus("waiting")

        while self.pyfile.waitUntil > time():
            self.thread.m.reconnecting.wait(2)
            self.checkAbort()
            if self.thread.m.reconnecting.isSet():
                self.waiting = False
                self.wantReconnect = False
                raise Reconnect

        self.waiting = False
        self.pyfile.setStatus("starting")

    def offline(self):
        """ fail and indicate file is offline """
        raise Fail("offline")

    def tempOffline(self):
        """ fail and indicates file ist temporary offline, the core may take consequences """
        raise Fail("temp. offline")

    def retry(self, max_tries=3, wait_time=1, reason="", backoff=lambda x, y: x):
        """Retries and begin again from the beginning

        :param max_tries: number of maximum retries
        :param wait_time: time to wait in seconds
        :param reason: reason for retrying, will be passed to fail if max_tries reached
        :param backoff: Function to backoff the wait time, takes initial time and number of retry as argument.
                        defaults to no backoff / fixed wait time
        """
        if 0 < max_tries <= self.retries:
            if not reason: reason = "Max retries reached"
            raise Fail(reason)

        self.wantReconnect = False
        self.retries += 1
        self.setWait(backoff(wait_time, self.retries))
        self.wait()

        raise Retry(reason)

    def download(self, url, get={}, post={}, ref=True, cookies=True, disposition=False):
        """Downloads the content at url to download folder

        :param disposition: if True and server provides content-disposition header\
        the filename will be changed if needed
        :return: The location where the file was saved
        """
        self.checkForSameFiles()
        self.checkAbort()

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
                except Exception as e:
                    self.log.warning(_("Setting User and Group failed: %s") % str(e))

        # convert back to unicode
        location = fs_decode(location)
        name = self.pyfile.name

        filename = join(location, name)

        self.core.addonManager.dispatchEvent("download:start", self.pyfile, url, filename)

        # Create the class used for downloading
        self.dl = self.core.requestFactory.getDownloadRequest(self.req, self.DOWNLOAD_CLASS)
        try:
            # TODO: hardcoded arguments
            newname = self.dl.download(url, filename, get=get, post=post, referer=ref, chunks=self.getChunkCount(),
                                       resume=self.resumeDownload, cookies=cookies, disposition=disposition)
        finally:
            self.dl.close()
            self.pyfile.size = self.dl.size

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
            except Exception as e:
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

        if api_size and api_size <= size:
            return None
        elif size > max_size and not read_size:
            return None
        self.log.debug("Download Check triggered")
        f = open(lastDownload, "rb")
        content = f.read(read_size if read_size else -1)
        f.close()
        #produces encoding errors, better log to other file in the future?
        #self.log.debug("Content: %s" % content)
        for name, rule in rules.items():
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

        for pyfile in self.core.files.cachedFiles():
            if pyfile != self.pyfile and pyfile.name == self.pyfile.name and pyfile.package().folder == pack.folder:
                if pyfile.status in (0, 12): #finished or downloading
                    raise SkipDownload(pyfile.pluginname)
                elif pyfile.status in (
                    5, 7) and starting: #a download is waiting/starting and was apparently started before
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
        if hasattr(self, "dl"):
            del self.dl
        if hasattr(self, "thread"):
            del self.thread
        if hasattr(self, "html"):
            del self.html
