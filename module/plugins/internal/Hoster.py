# -*- coding: utf-8 -*-

from __future__ import with_statement

import inspect
import os
import random
import time
import traceback
import urlparse

from module.plugins.internal.Captcha import Captcha
from module.plugins.internal.Plugin import (Plugin, Abort, Fail, Reconnect, Retry, Skip,
                                            chunks, encode, exists, fixurl as _fixurl, replace_patterns,
                                            seconds_to_midnight, set_cookie, set_cookies, parse_html_form,
                                            parse_html_tag_attr_value, timestamp)
from module.utils import fs_decode, fs_encode, save_join as fs_join, save_path as safe_filename


#@TODO: Remove in 0.4.10
def parse_fileInfo(klass, url="", html=""):
    info = klass.get_info(url, html)
    return info['name'], info['size'], info['status'], info['url']


#@TODO: Remove in 0.4.10
def getInfo(urls):
    #: result = [ .. (name, size, status, url) .. ]
    pass


#@TODO: Remove in 0.4.10
def create_getInfo(klass):
    def get_info(urls):
        for url in urls:
            if hasattr(klass, "URL_REPLACEMENTS"):
                url = replace_patterns(url, klass.URL_REPLACEMENTS)
            yield parse_fileInfo(klass, url)

    return get_info


class Hoster(Plugin):
    __name__    = "Hoster"
    __type__    = "hoster"
    __version__ = "0.18"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.org" ),
                       ("spoob"         , "spoob@pyload.org" ),
                       ("mkaay"         , "mkaay@mkaay.de"   ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, pyfile):
        self._init(pyfile.m.core)

        #: Engage wan reconnection
        self.wantReconnect = False  #@TODO: Change to `want_reconnect` in 0.4.10

        #: Enable simultaneous processing of multiple downloads
        self.multiDL = True  #@TODO: Change to `multi_dl` in 0.4.10
        self.limitDL = 0     #@TODO: Change to `limit_dl` in 0.4.10

        #: time.time() + wait in seconds
        self.wait_until = 0
        self.waiting    = False

        #: Account handler instance, see :py:class:`Account`
        self.account = None
        self.user    = None
        self.req     = None  #: Browser instance, see `network.Browser`

        #: Associated pyfile instance, see `PyFile`
        self.pyfile = pyfile

        self.thread = None  #: Holds thread in future

        #: Location where the last call to download was saved
        self.last_download = ""

        #: Re match of the last call to `checkDownload`
        self.last_check = None

        #: Js engine, see `JsEngine`
        self.js = self.pyload.js

        #: Captcha stuff
        self.captcha = Captcha(self)

        #: Some plugins store html code here
        self.html = None

        #: Dict of the amount of retries already made
        self.retries    = {}
        self.retry_free = False  #@TODO: Recheck in 0.4.10

        self._setup()
        self.init()


    @classmethod
    def get_info(cls, url="", html=""):
        url   = _fixurl(url)
        url_p = urlparse.urlparse(url)
        return {'name'  : (url_p.path.split('/')[-1] or
                            url_p.query.split('=', 1)[::-1][0].split('&', 1)[0] or
                                url_p.netloc.split('.', 1)[0]),
                'size'  : 0,
                'status': 3 if url else 8,
                'url'   : url}


    def init(self):
        """
        Initialize the plugin (in addition to `__init__`)
        """
        pass


    def setup(self):
        """
        Setup for enviroment and other things, called before downloading (possibly more than one time)
        """
        pass


    def _setup(self):
        if self.account:
            self.req             = self.pyload.requestFactory.getRequest(self.__name__, self.user)
            self.chunk_limit     = -1  #: -1 for unlimited
            self.resume_download = True
            self.premium         = self.account.is_premium(self.user)
        else:
            self.req             = self.pyload.requestFactory.getRequest(self.__name__)
            self.chunk_limit     = 1
            self.resume_download = False
            self.premium         = False


    def load_account(self):
        if self.req:
            self.req.close()

        if not self.account:
            self.account = self.pyload.accountManager.getAccountPlugin(self.__name__)

        if self.account:
            if not self.user:
                self.user = self.account.select()[0]

            if not self.user or not self.account.is_logged(self.user, True):
                self.account = False


    def preprocessing(self, thread):
        """
        Handles important things to do before starting
        """
        self.thread = thread

        if self.retry_free:
            self.account = False
        else:
            self.load_account()  #@TODO: Move to PluginThread in 0.4.10
            self.retry_free = False

        self._setup()
        self.setup()

        self.pyload.hookManager.downloadPreparing(self.pyfile)  #@TODO: Recheck in 0.4.10

        if self.pyfile.abort:
            self.abort()

        self.pyfile.setStatus("starting")
        self.log_debug("PROCESS URL " + self.pyfile.url, "PLUGIN VERSION %s" % self.__version__)

        return self.process(self.pyfile)


    def process(self, pyfile):
        """
        The 'main' method of every plugin, you **have to** overwrite it
        """
        raise NotImplementedError


    def set_reconnect(self, reconnect):
        reconnect = bool(reconnect)

        self.log_info(_("RECONNECT ") + ("enabled" if reconnect else "disabled"))
        self.log_debug("Previous wantReconnect: %s" % self.wantReconnect)

        self.wantReconnect = reconnect


    def set_wait(self, seconds, reconnect=None):
        """
        Set a specific wait time later used with `wait`

        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
        wait_time  = max(int(seconds), 1)
        wait_until = time.time() + wait_time + 1

        self.log_info(_("WAIT %d seconds") % wait_time)
        self.log_debug("Previous waitUntil: %f" % self.pyfile.waitUntil)

        self.pyfile.waitUntil = wait_until

        if reconnect is not None:
            self.set_reconnect(reconnect)


    def wait(self, seconds=None, reconnect=None):
        """
        Waits the time previously set
        """
        pyfile = self.pyfile

        if seconds is not None:
            self.set_wait(seconds)

        if reconnect is not None:
            self.set_reconnect(reconnect)

        self.waiting = True

        status = pyfile.status  #@NOTE: Remove in 0.4.10
        pyfile.setStatus("waiting")

        if not self.wantReconnect or self.account:
            if self.account:
                self.log_warning("Ignore reconnection due logged account")

            while pyfile.waitUntil > time.time():
                if pyfile.abort:
                    self.abort()

                time.sleep(2)

        else:
            while pyfile.waitUntil > time.time():
                if pyfile.abort:
                    self.abort()

                if self.thread.m.reconnecting.isSet():
                    self.waiting = False
                    self.wantReconnect = False
                    raise Reconnect

                self.thread.m.reconnecting.wait(2)
                time.sleep(2)

        self.waiting = False
        pyfile.status = status  #@NOTE: Remove in 0.4.10


    def skip(self, reason=""):
        """
        Skip and give reason
        """
        raise Skip(encode(reason))  #@TODO: Remove `encode` in 0.4.10


    def abort(self, reason=""):
        """
        Abort and give reason
        """
        #@TODO: Remove in 0.4.10
        if reason:
            self.pyfile.error = encode(reason)

        raise Abort


    def offline(self, reason=""):
        """
        Fail and indicate file is offline
        """
        #@TODO: Remove in 0.4.10
        if reason:
            self.pyfile.error = encode(reason)

        raise Fail("offline")


    def temp_offline(self, reason=""):
        """
        Fail and indicates file ist temporary offline, the core may take consequences
        """
        #@TODO: Remove in 0.4.10
        if reason:
            self.pyfile.error = encode(reason)

        raise Fail("temp. offline")


    def retry(self, max_tries=5, wait_time=1, reason=""):
        """
        Retries and begin again from the beginning

        :param max_tries: number of maximum retries
        :param wait_time: time to wait in seconds
        :param reason: reason for retrying, will be passed to fail if max_tries reached
        """
        id = inspect.currentframe().f_back.f_lineno
        if id not in self.retries:
            self.retries[id] = 0

        if 0 < max_tries <= self.retries[id]:
            self.fail(reason or _("Max retries reached"))

        self.wait(wait_time, False)

        self.retries[id] += 1
        raise Retry(encode(reason))  #@TODO: Remove `encode` in 0.4.10


    def restart(self, reason=None, nopremium=False):
        if not reason:
            reason = _("Fallback to free download") if nopremium else _("Restart")

        if nopremium:
            if self.premium:
                self.retry_free = True
            else:
                self.fail(reason, _("Download was already free"))

        raise Retry(encode(reason))  #@TODO: Remove `encode` in 0.4.10


    def fixurl(self, url):
        url = _fixurl(url)

        if not urlparse.urlparse(url).scheme:
            url_p = urlparse.urlparse(self.pyfile.url)
            baseurl = "%s://%s" % (url_p.scheme, url_p.netloc)
            url = urlparse.urljoin(baseurl, url)

        return url


    def download(self, url, get={}, post={}, ref=True, cookies=True, disposition=True):
        """
        Downloads the content at url to download folder

        :param url:
        :param get:
        :param post:
        :param ref:
        :param cookies:
        :param disposition: if True and server provides content-disposition header\
        the filename will be changed if needed
        :return: The location where the file was saved
        """
        if self.pyfile.abort:
            self.abort()

        url = self.fixurl(url)

        if not url or not isinstance(url, basestring):
            self.fail(_("No url given"))

        if self.pyload.debug:
            self.log_debug("DOWNLOAD URL " + url,
                           *["%s=%s" % (key, val) for key, val in locals().items() if key not in ("self", "url")])

        name = _fixurl(self.pyfile.name)
        self.pyfile.name = urlparse.urlparse(name).path.split('/')[-1] or name

        self.captcha.correct()
        self.check_for_same_files()

        self.pyfile.setStatus("downloading")

        download_folder   = self.pyload.config.get("general", "download_folder")
        download_location = fs_join(download_folder, self.pyfile.package().folder)

        if not exists(download_location):
            try:
                os.makedirs(download_location)
            except Exception, e:
                self.fail(e)

        self.set_permissions(download_location)

        location = fs_decode(download_location)
        filename = os.path.join(location, safe_filename(self.pyfile.name))  #@TODO: Move `safe_filename` check to HTTPDownload in 0.4.10

        self.pyload.hookManager.dispatchEvent("download_start", self.pyfile, url, filename)

        if self.pyfile.abort:
            self.abort()

        try:
            newname = self.req.httpDownload(url, filename, get=get, post=post, ref=ref, cookies=cookies,
                                            chunks=self.get_chunk_count(), resume=self.resume_download,
                                            progressNotify=self.pyfile.setProgress, disposition=disposition)
        finally:
            self.pyfile.size = self.req.size

        #@TODO: Recheck in 0.4.10
        if disposition and newname:
            finalname = urlparse.urlparse(newname).path.split('/')[-1].split(' filename*=')[0]

            if finalname != newname != self.pyfile.name:
                try:
                    os.rename(fs_join(location, newname), fs_join(location, finalname))

                except OSError, e:
                    self.log_warning(_("Error renaming `%s` to `%s`") % (newname, finalname), e)
                    finalname = newname

                self.log_info(_("`%s` saved as `%s`") % (self.pyfile.name, finalname))
                self.pyfile.name = finalname
                filename = os.path.join(location, finalname)

        self.set_permissions(fs_encode(filename))

        self.last_download = filename

        return self.last_download


    def check_download(self, rules, delete=False, file_size=0, size_tolerance=1024, read_size=1048576):
        """
        Checks the content of the last downloaded file, re match is saved to `lastCheck`

        :param rules: dict with names and rules to match (compiled regexp or strings)
        :param delete: delete if matched
        :param file_size: expected file size
        :param size_tolerance: size check tolerance
        :param read_size: amount of bytes to read from files
        :return: dictionary key of the first rule that matched
        """
        do_delete = False
        last_download = fs_encode(self.last_download)

        if not self.last_download or not exists(last_download):
            self.last_download = ""
            self.fail(self.pyfile.error or _("No file downloaded"))

        try:
            download_size = os.stat(last_download).st_size

            if download_size < 1:
                do_delete = True
                self.fail(_("Empty file"))

            elif file_size > 0:
                diff = abs(file_size - download_size)

                if diff > size_tolerance:
                    do_delete = True
                    self.fail(_("File size mismatch | Expected file size: %s | Downloaded file size: %s")
                              % (file_size, download_size))

                elif diff != 0:
                    self.log_warning(_("File size is not equal to expected size"))

            with open(last_download, "rb") as f:
                content = f.read(read_size)

            #: Produces encoding errors, better log to other file in the future?
            # self.log_debug("Content: %s" % content)
            for name, rule in rules.items():
                if isinstance(rule, basestring):
                    if rule in content:
                        do_delete = True
                        return name

                elif hasattr(rule, "search"):
                    m = rule.search(content)
                    if m:
                        do_delete = True
                        self.last_check = m
                        return name
        finally:
            if delete and do_delete:
                try:
                    os.remove(last_download)

                except OSError, e:
                    self.log_warning(_("Error removing: %s") % last_download, e)
                    if self.pyload.debug:
                        traceback.print_exc()

                else:
                    self.last_download = ""
                    self.log_info(_("File deleted"))


    def direct_link(self, url, follow_location=None):
        link = ""

        if follow_location is None:
            redirect = 1

        elif type(follow_location) is int:
            redirect = max(follow_location, 1)

        else:
            redirect = self.get_config("maxredirs", 10, "UserAgentSwitcher")

        for i in xrange(redirect):
            try:
                self.log_debug("Redirect #%d to: %s" % (i, url))
                header = self.load(url, just_header=True)

            except Exception:  #: Bad bad bad... rewrite this part in 0.4.10
                res = self.load(url,
                                just_header=True,
                                req=self.pyload.requestFactory.getRequest())

                header = {'code': req.code}
                for line in res.splitlines():
                    line = line.strip()
                    if not line or ":" not in line:
                        continue

                    key, none, value = line.partition(":")
                    key              = key.lower().strip()
                    value            = value.strip()

                    if key in header:
                        if type(header[key]) is list:
                            header[key].append(value)
                        else:
                            header[key] = [header[key], value]
                    else:
                        header[key] = value

            if 'content-disposition' in header:
                link = url

            elif 'location' in header and header['location']:
                location = header['location']

                if not urlparse.urlparse(location).scheme:
                    url_p    = urlparse.urlparse(url)
                    baseurl  = "%s://%s" % (url_p.scheme, url_p.netloc)
                    location = urlparse.urljoin(baseurl, location)

                if 'code' in header and header['code'] == 302:
                    link = location

                if follow_location:
                    url = location
                    continue

            else:
                extension = os.path.splitext(urlparse.urlparse(url).path.split('/')[-1])[-1]

                if 'content-type' in header and header['content-type']:
                    mimetype = header['content-type'].split(';')[0].strip()

                elif extension:
                    mimetype = mimetypes.guess_type(extension, False)[0] or "application/octet-stream"

                else:
                    mimetype = ""

                if mimetype and (link or 'html' not in mimetype):
                    link = url
                else:
                    link = ""

            break

        else:
            try:
                self.log_error(_("Too many redirects"))
            except Exception:
                pass

        return link


    def parse_html_form(self, attr_str="", input_names={}):
        return parse_html_form(attr_str, self.html, input_names)


    def check_traffic_left(self):
        if not self.account:
            return True

        traffic = self.account.get_data(self.user, True)['trafficleft']

        if traffic is None:
            return False
        elif traffic == -1:
            return True
        else:
            size = self.pyfile.size / 1024
            self.log_info(_("Filesize: %s KiB, Traffic left for user %s: %s KiB") % (size, self.user, traffic))
            return size <= traffic


    def get_password(self):
        """
        Get the password the user provided in the package
        """
        return self.pyfile.package().password or ""


    #: Deprecated method, use `check_for_same_files` instead (Remove in 0.4.10)
    def checkForSameFiles(self, *args, **kwargs):
        return self.check_for_same_files(*args, **kwargs)


    def check_for_same_files(self, starting=False):
        """
        Checks if same file was/is downloaded within same package

        :param starting: indicates that the current download is going to start
        :raises Skip:
        """
        pack = self.pyfile.package()

        for pyfile in self.pyload.files.cache.values():
            if pyfile != self.pyfile and pyfile.name is self.pyfile.name and pyfile.package().folder is pack.folder:
                if pyfile.status in (0, 12):  #: Finished or downloading
                    self.skip(pyfile.pluginname)
                elif pyfile.status in (5, 7) and starting:  #: A download is waiting/starting and was appenrently started before
                    self.skip(pyfile.pluginname)

        download_folder = self.pyload.config.get("general", "download_folder")
        location = fs_join(download_folder, pack.folder, self.pyfile.name)

        if starting and self.pyload.config.get("download", "skip_existing") and exists(location):
            size = os.stat(location).st_size
            if size >= self.pyfile.size:
                self.skip("File exists")

        pyfile = self.pyload.db.findDuplicates(self.pyfile.id, self.pyfile.package().folder, self.pyfile.name)
        if pyfile:
            if exists(location):
                self.skip(pyfile[0])

            self.log_debug("File %s not skipped, because it does not exists." % self.pyfile.name)
