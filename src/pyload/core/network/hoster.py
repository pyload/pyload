# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import time
from builtins import int, str

from future import standard_library

from pyload.requests.curl.download import CurlDownload
from pyload.requests.curl.request import CurlRequest
from pyload.utils.fs import lopen, makedirs, remove

from .base import Base, Fail, Retry

standard_library.install_aliases()


if os.name != 'nt':
    import grp
    import pwd


class Reconnect(Exception):
    """
    Raised when reconnected.
    """
    __slots__ = []


class Skip(Exception):
    """
    Raised when download should be skipped.
    """
    __slots__ = []


class Hoster(Base):
    """
    Base plugin for hoster plugin. Overwrite get_info for online status retrieval, process for downloading.
    """
    # Class used to make requests with `self.load`
    REQUEST_CLASS = CurlRequest

    # Class used to make download
    DOWNLOAD_CLASS = CurlDownload

    @staticmethod
    def get_info(urls):
        """
        This method is used to retrieve the online status of files for hoster plugins.

        :param urls: List of urls
        :return: yield list of :class:`LinkStatus` as result
        """
        pass

    __type__ = "hoster"

    def __init__(self, file):
        # TODO: file.owner, but it's not correct yet
        Base.__init__(self, file.manager.pyload)

        self.want_reconnect = False
        # enables simultaneous processing of multiple downloads
        self.limit_dl = 0
        # chunk limit
        self.chunk_limit = 1
        # enables resume (will be ignored if server dont accept chunks)
        self.resume_download = False

        # plugin is waiting
        self.waiting = False

        self.ocr = None  # captcha reader instance
        # account handler instance, see :py:class:`Account`
        self.account = self.pyload_core.acm.select_account(
            self.__name__, self.owner)

        # premium status
        self.premium = False

        if self.account:
            # Request instance bound to account
            self.req = self.account.get_account_request()
            # Default:  -1, True, True
            self.chunk_limit, self.limit_dl, self.resume_download = self.account.get_download_settings()
            self.premium = self.account.is_premium()
        else:
            self.req = self.pyload_core.req.get_request(class_=self.REQUEST_CLASS)

        # Will hold the download class
        self.dl = None

        # associated file instance, see `File`
        self.filename = file
        self.thread = None  # holds thread in future

        # location where the last call to download was saved
        self.last_download = ""
        # re match of the last call to `check_download`
        self.last_check = None

        self.retries = 0  # amount of retries already made
        self.html = None  # some plugins store html code here

        self.init()

    @property
    def user(self):
        self.log_debug(
            "Deprecated usage of self.user -> use self.account.loginname")
        if self.account:
            return self.account.loginname

    def get_multi_dl(self):
        return self.limit_dl <= 0

    def set_multi_dl(self, val):
        self.limit_dl = 0 if val else 1

    # virtual attribute using self.limit_dl on behind
    multi_dl = property(get_multi_dl, set_multi_dl)

    def get_chunk_count(self):
        if self.chunk_limit <= 0:
            return self.pyload_core.config.get('connection', 'max_chunks')
        return min(self.pyload_core.config.get(
            'connection', 'max_chunks'), self.chunk_limit)

    def get_download_limit(self):
        if self.account:
            limit = self.account.options.get("limitDL", 0)
            if limit == "":
                limit = 0
            if self.limit_dl > 0:  # a limit is already set, we use the minimum
                return min(int(limit), self.limit_dl)
            else:
                return int(limit)
        else:
            return self.limit_dl

    def __call__(self):
        return self.__name__

    def init(self):
        """
        Initialize the plugin (in addition to `__init__`).
        """
        pass

    def setup(self):
        """
        Setup for environment and other things, called before downloading (possibly more than one time).
        """
        pass

    def preprocessing(self, thread):
        """
        Handles important things to do before starting.
        """
        self.thread = thread

        if self.account:
            # will force a re-login or reload of account info if necessary
            self.account.get_account_info()
        else:
            self.req.reset()

        self.setup()

        self.file.set_status("starting")

        return self.process(self.file)

    def process(self, file):
        """
        The 'main' method of every plugin, you **have to** overwrite it.
        """
        raise NotImplementedError

    def abort(self):
        return self.file.abort

    def reset_account(self):
        """
        Don't use account and retry download.
        """
        self.account = None
        self.req = self.pyload_core.req.get_request(self.__name__)
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
        # TODO: checksum check addon
        return True, 10

    def set_wait(self, seconds, reconnect=None):
        """
        Set a specific wait time later used with `wait`

        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
        if reconnect is not None:
            self.want_reconnect = reconnect
        self.file.wait_until = time.time() + int(seconds)

    def wait(self, seconds=None, reconnect=None):
        """
        Waits the time previously set or use these from arguments. See `set_wait`.
        """
        if seconds is not None:
            self.set_wait(seconds, reconnect)

        self._wait()

    def _wait(self):
        self.waiting = True
        self.file.set_status("waiting")

        while self.file.wait_until > time.time():
            self.thread.manager.reconnecting.wait(2)
            self.check_abort()
            if self.thread.manager.reconnecting.isSet():
                self.waiting = False
                self.want_reconnect = False
                raise Reconnect

        self.waiting = False
        self.file.set_status("starting")

    def offline(self):
        """
        Fail and indicate file is offline.
        """
        raise Fail("offline")

    def temp_offline(self):
        """
        Fail and indicates file ist temporary offline, the core may take consequences.
        """
        raise Fail("temp. offline")

    def retry(self, max_tries=3, wait_time=1,
              reason="", backoff=lambda x, y: x):
        """
        Retries and begin again from the beginning

        :param max_tries: number of maximum retries
        :param wait_time: time to wait in seconds
        :param reason: reason for retrying, will be passed to fail if max_tries reached
        :param backoff: Function to backoff the wait time, takes initial time and number of retry as argument.
                        defaults to no backoff / fixed wait time
        """
        if 0 < max_tries <= self.retries:
            if not reason:
                reason = "Max retries reached"
            raise Fail(reason)

        self.want_reconnect = False
        self.retries += 1
        self.set_wait(backoff(wait_time, self.retries))
        self.wait()

        raise Retry(reason)

    def download(self, url, get={}, post={}, ref=True,
                 cookies=True, disposition=False):
        """
        Downloads the content at url to download folder

        :param disposition: if True and server provides content-disposition header
        the filename will be changed if needed
        :return: The location where the file was saved
        """
        self.check_for_same_files()
        self.check_abort()

        self.file.set_status("downloading")

        download_folder = self.pyload_core.config.get('general', 'storage_folder')

        location = os.path.join(download_folder, self.file.package().folder)

        if not os.path.isdir(location):
            mode = int(self.pyload_core.config.get('permission', 'foldermode'), 8)
            makedirs(location, mode, exist_ok=True)

            if self.pyload_core.config.get(
                    'permission', 'change_fileowner') and os.name != 'nt':
                try:
                    uid = pwd.getpwnam(self.pyload_core.config.get(
                        'permission', 'user'))[2]
                    gid = grp.getgrnam(self.pyload_core.config.get(
                        'permission', 'group'))[2]

                    os.chown(location, uid, gid)
                except Exception as e:
                    self.pyload_core.log.warning(
                        self._("Setting User and Group failed: {0}").format(
                            str(e)))

        name = self.file.name

        filepath = os.path.join(location, name)

        self.pyload_core.adm.fire("download:start", self.file, url, filepath)

        # Create the class used for downloading
        self.dl = self.pyload_core.req.get_download_request(
            self.req, self.DOWNLOAD_CLASS)
        try:
            # TODO: hardcoded arguments
            newname = self.dl.download(
                url, filepath, get=get, post=post, referer=ref,
                chunks=self.get_chunk_count(),
                resume=self.resume_download, cookies=cookies,
                disposition=disposition)
        finally:
            self.dl.close()
            self.file.size = self.dl.size

        if disposition and newname and newname != name:  # triple check, just to be sure
            self.pyload_core.log.info(
                self._("{0} saved as {1}").format(name, newname))
            self.file.name = newname
            filepath = os.path.join(location, newname)

        fs_filename = filepath

        if self.pyload_core.config.get('permission', 'change_filemode'):
            os.chmod(fs_filename, int(self.pyload_core.config.get(
                'permission', 'filemode'), 8))

        if self.pyload_core.config.get(
                'permission', 'change_fileowner') and os.name != 'nt':
            try:
                uid = pwd.getpwnam(
                    self.pyload_core.config.get(
                        'permission', 'user'))[2]
                gid = grp.getgrnam(self.pyload_core.config.get(
                    'permission', 'group'))[2]

                os.chown(fs_filename, uid, gid)
            except Exception as e:
                self.pyload_core.log.warning(
                    self._("Setting User and Group failed: {0}").format(
                        str(e)))

        self.last_download = fs_filename
        return self.last_download

    def check_download(self, rules, api_size=0,
                       max_size=50000, delete=True, read_size=0):
        """
        Checks the content of the last downloaded file, re match is saved to `last_check`

        :param rules: dict with names and rules to match (compiled regexp or strings)
        :param api_size: expected file size
        :param max_size: if the file is larger then it wont be checked
        :param delete: delete if matched
        :param read_size: amount of bytes to read from files larger then max_size
        :return: dictionary key of the first rule that matched
        """
        if not os.path.isfile(self.last_download):
            return None

        size = os.stat(self.last_download)
        size = size.st_size

        if api_size and api_size <= size:
            return None
        elif size > max_size and not read_size:
            return None
        self.pyload_core.log.debug("Download Check triggered")
        with lopen(self.last_download, mode='rb') as fp:
            content = fp.read(read_size if read_size else -1)
        # produces encoding errors, better log to other file in the future?
        #self.pyload_core.log.debug("Content: {0}".format(content))
        for name, rule in rules.items():
            if isinstance(rule, str):
                if rule in content:
                    if delete:
                        remove(self.last_download, trash=True)
                    return name
            elif hasattr(rule, "search"):
                m = rule.search(content)
                if m is not None:
                    if delete:
                        remove(self.last_download, trash=True)
                    self.last_check = m
                    return name

    def get_password(self):
        """
        Get the password the user provided in the package.
        """
        password = self.file.package().password
        if not password:
            return ""
        return password

    def check_for_same_files(self, starting=False):
        """
        Checks if same file was/is downloaded within same package

        :param starting: indicates that the current download is going to start
        :raises Skip:
        """
        pack = self.file.package()

        for file in self.pyload_core.files.cached_files():
            if file != self.file and file.name == self.file.name and file.package(
            ).folder == pack.folder:
                if file.status in (0, 12):  # finished or downloading
                    raise Skip(file.pluginname)
                elif file.status in (
                        5, 7) and starting:  # a download is waiting/starting and was apparently started before
                    raise Skip(file.pluginname)

        download_folder = self.pyload_core.config.get('general', 'storage_folder')
        location = os.path.join(download_folder, pack.folder, self.file.name)

        if starting and self.pyload_core.config.get(
                'connection', 'skip') and os.path.isfile(location):
            size = os.stat(location).st_size
            if size >= self.file.size:
                raise Skip("File exists")

        file = self.pyload_core.db.find_duplicates(
            self.file.fid, self.file.package().folder, self.file.name)
        if file:
            if os.path.isfile(location):
                raise Skip(file[0])

            self.pyload_core.log.debug(
                "File {0} not skipped, because it does not exists".format(
                    self.file.name))

    def clean(self):
        """
        Clean everything and remove references.
        """
        if hasattr(self, "file"):
            del self.file
        if hasattr(self, "req"):
            self.req.close()
            del self.req
        if hasattr(self, "dl"):
            del self.dl
        if hasattr(self, "thread"):
            del self.thread
        if hasattr(self, "html"):
            del self.html
