# -*- coding: utf-8 -*-

from __future__ import with_statement

import inspect
import os
import random
import time
import urlparse

if os.name != "nt":
    import grp
    import pwd

from module.plugins.internal.Plugin import (Plugin, Abort, Fail, Reconnect, Retry, Skip
                                            chunks, fixurl as _fixurl, replace_patterns, seconds_to_midnight,
                                            set_cookies, parse_html_form, parse_html_tag_attr_value,
                                            timestamp)
from module.utils import fs_decode, fs_encode, save_join as fs_join


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
    __version__ = "0.05"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.org" ),
                       ("spoob"         , "spoob@pyload.org" ),
                       ("mkaay"         , "mkaay@mkaay.de"   ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, pyfile):
        super(Hoster, self).__init__(pyfile.m.core)

        #: Engage wan reconnection
        self.want_reconnect = False

        #: Enable simultaneous processing of multiple downloads
        self.multi_dl = True
        self.limit_dl = 0

        #: Chunk limit
        self.chunk_limit = 1
        self.resume_download = False

        #: time.time() + wait in seconds
        self.wait_until = 0
        self.waiting = False

        #: Captcha reader instance
        self.ocr = None

        #: Account handler instance, see :py:class:`Account`
        self.account = pyfile.m.core.accountManager.getAccountPlugin(self.__name__)

        #: Premium status
        self.premium = False

        #: username/login
        self.user = None

        if self.account and not self.account.can_use():
            self.account = None

        if self.account:
            self.user, data = self.account.select_account()

            #: Browser instance, see `network.Browser`
            self.req = self.account.get_account_request(self.user)
            self.chunk_limit = -1  #: Chunk limit, -1 for unlimited

            #: Enables resume (will be ignored if server dont accept chunks)
            self.resume_download = True

            #: Premium status
            self.premium = self.account.is_premium(self.user)
        else:
            self.req = pyfile.m.core.requestFactory.getRequest(self.__name__)

        #: Associated pyfile instance, see `PyFile`
        self.pyfile = pyfile

        self.thread = None  #: Holds thread in future

        #: Location where the last call to download was saved
        self.last_download = ""

        #: Re match of the last call to `checkDownload`
        self.last_check = None

        #: Js engine, see `JsEngine`
        self.js = self.core.js

        #: Captcha task
        self.c_task = None

        #: Some plugins store html code here
        self.html = None

        #: Dict of the amount of retries already made
        self.retries = {}

        self.init()


    @classmethod
    def get_info(cls, url="", html=""):
        url   = _fixurl(url)
        url_p = urlparse.urlparse(url)
        return {'name'  : (url_p.path.split('/')[-1]
                           or url_p.query.split('=', 1)[::-1][0].split('&', 1)[0]
                           or url_p.netloc.split('.', 1)[0]),
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


    def preprocessing(self, thread):
        """
        Handles important things to do before starting
        """
        self.thread = thread

        self.req.renewHTTPRequest()

        if self.account:
            self.account.check_login(self.user)
        else:
            self.req.clearCookies()

        self.setup()

        self.pyfile.setStatus("starting")

        return self.process(self.pyfile)


    def process(self, pyfile):
        """
        The 'main' method of every plugin, you **have to** overwrite it
        """
        raise NotImplementedError


    def get_chunk_count(self):
        if self.chunk_limit <= 0:
            return self.core.config.get("download", "chunks")
        return min(self.core.config.get("download", "chunks"), self.chunk_limit)


    def reset_account(self):
        """
        Don't use account and retry download
        """
        self.account = None
        self.req = self.core.requestFactory.getRequest(self.__name__)
        self.retry()


    def set_reconnect(self, reconnect):
        reconnect = bool(reconnect)
        self.log_debug("Set wantReconnect to: %s (previous: %s)" % (reconnect, self.want_reconnect))
        self.want_reconnect = reconnect


    def set_wait(self, seconds, reconnect=None):
        """
        Set a specific wait time later used with `wait`

        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
        wait_time  = max(int(seconds), 1)
        wait_until = time.time() + wait_time + 1

        self.log_debug("Set waitUntil to: %f (previous: %f)" % (wait_until, self.pyfile.waitUntil),
                       "Wait: %d (+1) seconds" % wait_time)

        self.pyfile.waitUntil = wait_until

        if reconnect is not None:
            self.set_reconnect(reconnect)


    def wait(self, seconds=0, reconnect=None):
        """
        Waits the time previously set
        """
        pyfile = self.pyfile

        if seconds > 0:
            self.set_wait(seconds)

        if reconnect is not None:
            self.set_reconnect(reconnect)

        self.waiting = True

        status = pyfile.status
        pyfile.setStatus("waiting")

        self.log_info(_("Wait: %d seconds") % (pyfile.waitUntil - time.time()),
                      _("Reconnect: %s")    % self.want_reconnect)

        if self.account:
            self.log_debug("Ignore reconnection due account logged")

            while pyfile.waitUntil > time.time():
                if pyfile.abort:
                    self.abort()

                time.sleep(1)
        else:
            while pyfile.waitUntil > time.time():
                self.thread.m.reconnecting.wait(2)

                if pyfile.abort:
                    self.abort()

                if self.thread.m.reconnecting.isSet():
                    self.waiting = False
                    self.want_reconnect = False
                    raise Reconnect

                time.sleep(1)

        self.waiting = False

        pyfile.status = status


    def skip(self, reason=""):
        """
        Skip and give reason
        """
        raise Skip(fs_encode(reason))


    def abort(self, reason=""):
        """
        Abort and give reason
        """
        if reason:
            self.pyfile.error = fs_encode(reason)
        raise Abort


    def offline(self, reason=""):
        """
        Fail and indicate file is offline
        """
        if reason:
            self.pyfile.error = fs_encode(reason)
        raise Fail("offline")


    def temp_offline(self, reason=""):
        """
        Fail and indicates file ist temporary offline, the core may take consequences
        """
        if reason:
            self.pyfile.error = fs_encode(reason)
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
            self.fail(reason or _("Max retries reached"), _("retry"))

        self.wait(wait_time, False)

        self.retries[id] += 1
        raise Retry(reason)


    def invalid_captcha(self):
        self.log_error(_("Invalid captcha"))
        if self.c_task:
            self.c_task.invalid()


    def correct_captcha(self):
        self.log_info(_("Correct captcha"))
        if self.c_task:
            self.c_task.correct()


    def decrypt_captcha(self, url, get={}, post={}, cookies=False, forceUser=False,
                       imgtype='jpg', result_type='textual'):
        """
        Loads a captcha and decrypts it with ocr, plugin, user input

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

        id = ("%.2f" % time.time())[-6:].replace(".", "")

        with open(os.path.join("tmp", "tmpCaptcha_%s_%s.%s" % (self.__name__, id, imgtype)), "wb") as tmpCaptcha:
            tmpCaptcha.write(img)

        has_plugin = self.__name__ in self.core.pluginManager.ocrPlugins

        if self.core.captcha:
            Ocr = self.core.pluginManager.loadClass("ocr", self.__name__)
        else:
            Ocr = None

        if Ocr and not forceUser:
            time.sleep(random.randint(3000, 5000) / 1000.0)
            if self.pyfile.abort:
                self.abort()

            ocr = Ocr()
            result = ocr.get_captcha(tmpCaptcha.name)
        else:
            captchaManager = self.core.captchaManager
            task = captchaManager.newTask(img, imgtype, tmpCaptcha.name, result_type)
            self.c_task = task
            captchaManager.handleCaptcha(task)

            while task.isWaiting():
                if self.pyfile.abort:
                    captchaManager.removeTask(task)
                    self.abort()
                time.sleep(1)

            captchaManager.removeTask(task)

            if task.error and has_plugin:  #: Ignore default error message since the user could use OCR
                self.fail(_("Pil and tesseract not installed and no Client connected for captcha decrypting"))
            elif task.error:
                self.fail(task.error)
            elif not task.result:
                self.fail(_("No captcha result obtained in appropiate time by any of the plugins"))

            result = task.result
            self.log_debug("Received captcha result: %s" % result)

        if not self.core.debug:
            try:
                os.remove(tmpCaptcha.name)
            except Exception:
                pass

        return result


    def fixurl(self, url):
        url = _fixurl(url)

        if not urlparse.urlparse(url).scheme:
            url_p = urlparse.urlparse(self.pyfile.url)
            baseurl = "%s://%s" % (url_p.scheme, url_p.netloc)
            url = urlparse.urljoin(baseurl, url)

        return url


    def download(self, url, get={}, post={}, ref=True, cookies=True, disposition=False):
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

        if self.core.debug:
            self.log_debug("Download url " + url, *["%s=%s" % (key, val) for key, val in locals().iteritems() if key not in ("self", "url")])

        self.correct_captcha()
        self.check_for_same_files()

        self.pyfile.setStatus("downloading")

        if disposition:
            self.pyfile.name = urlparse.urlparse(url).path.split('/')[-1] or self.pyfile.name

        download_folder = self.core.config.get("general", "download_folder")

        location = fs_join(download_folder, self.pyfile.package().folder)

        if not os.path.exists(location):
            try:
                os.makedirs(location, int(self.core.config.get("permission", "folder"), 8))

                if self.core.config.get("permission", "change_dl") and os.name != "nt":
                    uid = pwd.getpwnam(self.core.config.get("permission", "user"))[2]
                    gid = grp.getgrnam(self.core.config.get("permission", "group"))[2]
                    os.chown(location, uid, gid)

            except Exception, e:
                self.fail(e)

        #: Convert back to unicode
        location = fs_decode(location)
        name = safe_filename(self.pyfile.name)

        filename = os.path.join(location, name)

        self.core.addonManager.dispatchEvent("download-start", self.pyfile, url, filename)

        try:
            newname = self.req.httpDownload(url, filename, get=get, post=post, ref=ref, cookies=cookies,
                                            chunks=self.get_chunk_count(), resume=self.resume_download,
                                            progressNotify=self.pyfile.setProgress, disposition=disposition)
        finally:
            self.pyfile.size = self.req.size

        if newname:
            newname = urlparse.urlparse(newname).path.split('/')[-1]

            if disposition and newname != name:
                self.log_info(_("%(name)s saved as %(newname)s") % {'name': name, 'newname': newname})
                self.pyfile.name = newname
                filename = os.path.join(location, newname)

        fs_filename = fs_encode(filename)

        if self.core.config.get("permission", "change_file"):
            try:
                os.chmod(fs_filename, int(self.core.config.get("permission", "file"), 8))
            except Exception, e:
                self.log_warning(_("Setting file mode failed"), e)

        if self.core.config.get("permission", "change_dl") and os.name != "nt":
            try:
                uid = pwd.getpwnam(self.core.config.get("permission", "user"))[2]
                gid = grp.getgrnam(self.core.config.get("permission", "group"))[2]
                os.chown(fs_filename, uid, gid)

            except Exception, e:
                self.log_warning(_("Setting User and Group failed"), e)

        self.last_download = filename
        return self.last_download


    def check_download(self, rules, delete=True, file_size=0, size_tolerance=1000, read_size=100000):
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
        lastDownload = fs_encode(self.last_download)

        if not self.last_download or not os.path.exists(lastDownload):
            self.last_download = ""
            self.fail(self.pyfile.error or _("No file downloaded"))

        try:
            download_size = os.stat(lastDownload).st_size

            if download_size < 1:
                do_delete = True
                self.fail(_("Empty file"))

            elif file_size > 0:
                diff = abs(file_size - download_size)

                if diff > size_tolerance:
                    do_delete = True
                    self.fail(_("File size mismatch"))

                elif diff != 0:
                    self.log_warning(_("File size is not equal to expected size"))

            self.log_debug("Download Check triggered")

            with open(lastDownload, "rb") as f:
                content = f.read(read_size)

            #: Produces encoding errors, better log to other file in the future?
            # self.log_debug("Content: %s" % content)
            for name, rule in rules.iteritems():
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
                os.remove(lastDownload)


    def direct_link(self, url, follow_location=None):
        link = ""

        if follow_location is None:
            redirect = 1

        elif type(follow_location) is int:
            redirect = max(follow_location, 1)

        else:
            redirect = self.get_config("maxredirs", plugin="UserAgentSwitcher")

        for i in xrange(redirect):
            try:
                self.log_debug("Redirect #%d to: %s" % (i, url))
                header = self.load(url, just_header=True)

            except Exception:  #: Bad bad bad... rewrite this part in 0.4.10
                req = pyreq.getHTTPRequest()
                res = self.load(url, just_header=True)

                req.close()

                header = {'code': req.code}
                for line in res.splitlines():
                    line = line.strip()
                    if not line or ":" not in line:
                        continue

                    key, none, value = line.partition(":")
                    key              = key.lower().strip()
                    value            = value.strip()

                    if key in header:
                        if type(header[key]) == list:
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

        traffic = self.account.get_account_info(self.user, True)['trafficleft']

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


    def check_for_same_files(self, starting=False):
        """
        Checks if same file was/is downloaded within same package

        :param starting: indicates that the current download is going to start
        :raises Skip:
        """
        pack = self.pyfile.package()

        for pyfile in self.core.files.cache.values():
            if pyfile != self.pyfile and pyfile.name == self.pyfile.name and pyfile.package().folder == pack.folder:
                if pyfile.status in (0, 12):  #: Finished or downloading
                    self.skip(pyfile.pluginname)
                elif pyfile.status in (5, 7) and starting:  #: A download is waiting/starting and was appenrently started before
                    self.skip(pyfile.pluginname)

        download_folder = self.core.config.get("general", "download_folder")
        location = fs_join(download_folder, pack.folder, self.pyfile.name)

        if starting and self.core.config.get("download", "skip_existing") and os.path.exists(location):
            size = os.stat(location).st_size
            if size >= self.pyfile.size:
                self.skip("File exists")

        pyfile = self.core.db.findDuplicates(self.pyfile.id, self.pyfile.package().folder, self.pyfile.name)
        if pyfile:
            if os.path.exists(location):
                self.skip(pyfile[0])

            self.log_debug("File %s not skipped, because it does not exists." % self.pyfile.name)


    def clean(self):
        """
        Clean everything and remove references
        """
        if hasattr(self, "pyfile"):
            del self.pyfile

        if hasattr(self, "req"):
            self.req.close()
            del self.req

        if hasattr(self, "thread"):
            del self.thread

        if hasattr(self, "html"):
            del self.html
