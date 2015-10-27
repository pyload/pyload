# -*- coding: utf-8 -*-

from __future__ import with_statement

import mimetypes
import os
import re

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.Base import Base, create_getInfo, parse_fileInfo
from module.plugins.internal.Plugin import Fail, Retry
from module.plugins.internal.utils import encode, exists, fixurl, fs_join, parse_name


class Hoster(Base):
    __name__    = "Hoster"
    __type__    = "hoster"
    __version__ = "0.45"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"   , "bool", "Activated"                                 , True),
                   ("use_premium" , "bool", "Use premium account if available"          , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails", True),
                   ("chk_filesize", "bool", "Check file size"                           , True)]

    __description__ = """Base hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init_base(self):
        #: Enable simultaneous processing of multiple downloads
        self.limitDL = 0  #@TODO: Change to `limit_dl` in 0.4.10

        #:
        self.chunk_limit = None

        #:
        self.resume_download = False

        #: Location where the last call to download was saved
        self.last_download = None

        #: Re match of the last call to `checkDownload`
        self.last_check = None

        #: Restart flag
        self.restart_free = False  #@TODO: Recheck in 0.4.10


    def setup_base(self):
        self.last_download = None
        self.last_check    = None
        self.restart_free  = False

        if self.account:
            self.chunk_limit     = -1  #: -1 for unlimited
            self.resume_download = True
        else:
            self.chunk_limit     = 1
            self.resume_download = False


    def load_account(self):
        if self.restart_free:
            self.account = False
            self.user    = None  #@TODO: Remove in 0.4.10
        else:
            super(Hoster, self).load_account()
            # self.restart_free = False


    def _process(self, thread):
        self.log_debug("Plugin version: " + self.__version__)
        self.log_debug("Plugin status: " + self.__status__)

        if self.__status__ is "broken":
            self.fail(_("Plugin is temporarily unavailable"))

        elif self.__status__ is "testing":
            self.log_warning(_("Plugin may be unstable"))

        self.thread = thread
        self._setup()

        # self.pyload.hookManager.downloadPreparing(self.pyfile)  #@TODO: Recheck in 0.4.10
        self.check_status()

        self.pyfile.setStatus("starting")

        try:
            self.process(self.pyfile)
            self.check_status()
            self.check_download()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            if self.get_config('fallback', True) and self.premium:
                self.log_warning(_("Premium download failed"), e)
                self.restart(premium=False)

            else:
                raise Fail(encode(e))


    def isdownload(self, url, resume=None, redirect=True):
        link      = False
        maxredirs = 10

        if resume is None:
            resume = self.resume_download

        if type(redirect) is int:
            maxredirs = max(redirect, 1)

        elif redirect:
            maxredirs = self.get_config("maxredirs", default=maxredirs, plugin="UserAgentSwitcher")

        for i in xrange(maxredirs):
            self.log_debug("Redirect #%d to: %s" % (i, url))

            header = self.load(url, just_header=True)

            if 'content-disposition' in header:
                link = url

            elif header.get('location'):
                location = self.fixurl(header.get('location'), url)
                code     = header.get('code')

                if code == 302:
                    link = location

                elif code == 301:
                    url = location
                    if redirect:
                        continue

                if resume:
                    url = location
                    continue

            else:
                mimetype    = ""
                contenttype = header.get('content-type')
                extension   = os.path.splitext(parse_name(url))[-1]

                if contenttype:
                    mimetype = contenttype.split(';')[0].strip()

                elif extension:
                    mimetype = mimetypes.guess_type(extension, False)[0] or "application/octet-stream"

                if mimetype and (link or 'html' not in mimetype):
                    link = url
                else:
                    link = False

            return link


    def download(self, url, get={}, post={}, ref=True, cookies=True, disposition=True, resume=None, chunks=None):
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
        self.check_status()

        if self.pyload.debug:
            self.log_debug("DOWNLOAD URL " + url,
                           *["%s=%s" % (key, val) for key, val in locals().items() if key not in ("self", "url", "_[1]")])

        dl_url      = self.fixurl(url)
        dl_basename = parse_name(self.pyfile.name)

        self.pyfile.name = dl_basename

        self.captcha.correct()

        if self.pyload.config.get("download", "skip_existing"):
            self.check_filedupe()

        self.pyfile.setStatus("downloading")

        dl_folder   = self.pyload.config.get("general", "download_folder")
        dl_dirname  = os.path.join(dl_folder, self.pyfile.package().folder)
        dl_filename = os.path.join(dl_dirname, dl_basename)

        dl_dir  = encode(dl_dirname)
        dl_file = encode(dl_filename)  #@TODO: Move safe-filename check to HTTPDownload in 0.4.10

        if not exists(dl_dir):
            try:
                os.makedirs(dl_dir)

            except Exception, e:
                self.fail(e)

        self.set_permissions(dl_dir)

        self.pyload.hookManager.dispatchEvent("download_start", self.pyfile, dl_url, dl_filename)
        self.check_status()

        dl_chunks   = self.pyload.config.get("download", "chunks")
        chunk_limit = chunks or self.chunk_limit or -1

        if dl_chunks is -1 or chunk_limit is -1:
            chunks = max(dl_chunks, chunk_limit)
        else:
            chunks = min(dl_chunks, chunk_limit)

        resume = self.resume_download if resume is None else bool(resume)

        try:
            newname = self.req.httpDownload(dl_url, dl_file, get=get, post=post, ref=ref,
                                            cookies=cookies, chunks=chunks, resume=resume,
                                            progressNotify=self.pyfile.setProgress,
                                            disposition=disposition)

        except BadHeader, e:
            self.req.code = e.code
            raise BadHeader(e)

        finally:
            self.pyfile.size = self.req.size

        if self.req.code in (404, 410):
            bad_file = fs_join(dl_dirname, newname)
            try:
                os.remove(bad_file)

            except OSError, e:
                self.log_debug(_("Error removing `%s`") % bad_file, e)

            else:
                return ""

        #@TODO: Recheck in 0.4.10
        if disposition and newname:
            safename = parse_name(newname.split(' filename*=')[0])

            if safename != newname:
                try:
                    old_file = fs_join(dl_dirname, newname)
                    new_file = fs_join(dl_dirname, safename)
                    os.rename(old_file, new_file)

                except OSError, e:
                    self.log_warning(_("Error renaming `%s` to `%s`")
                                     % (newname, safename), e)
                    safename = newname

                self.log_info(_("`%s` saved as `%s`") % (self.pyfile.name, safename))

            self.pyfile.name = safename

            dl_filename = os.path.join(dl_dirname, safename)
            dl_file = encode(dl_filename)

        self.set_permissions(dl_file)

        self.last_download = dl_filename

        return dl_filename


    def check_filesize(self, file_size, size_tolerance=1024):
        """
        Checks the file size of the last downloaded file

        :param file_size: expected file size
        :param size_tolerance: size check tolerance
        """
        if not self.last_download:
            return

        dl_location = encode(self.last_download)
        dl_size     = os.stat(dl_location).st_size

        if dl_size < 1:
            self.fail(_("Empty file"))

        elif file_size > 0:
            diff = abs(file_size - dl_size)

            if diff > size_tolerance:
                self.fail(_("File size mismatch | Expected file size: %s | Downloaded file size: %s")
                          % (file_size, dl_size))

            elif diff != 0:
                self.log_warning(_("File size is not equal to expected size"))


    def check_file(self, rules, delete=False, read_size=1048576, file_size=0, size_tolerance=1024):
        """
        Checks the content of the last downloaded file, re match is saved to `last_check`

        :param rules: dict with names and rules to match (compiled regexp or strings)
        :param delete: delete if matched
        :param file_size: expected file size
        :param size_tolerance: size check tolerance
        :param read_size: amount of bytes to read from files
        :return: dictionary key of the first rule that matched
        """
        do_delete = False
        last_download = encode(self.last_download)  #@TODO: Recheck in 0.4.10

        if not self.last_download or not exists(last_download):
            self.fail(self.pyfile.error or _("No file downloaded"))

        try:
            self.check_filesize(file_size, size_tolerance)

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
                    if m is not None:
                        do_delete = True
                        self.last_check = m
                        return name
        finally:
            if delete and do_delete:
                try:
                    os.remove(last_download)

                except OSError, e:
                    self.log_warning(_("Error removing `%s`") % last_download, e)

                else:
                    self.log_info(_("File deleted: ") + self.last_download)
                    self.last_download = ""  #: Recheck in 0.4.10


    def check_download(self):
        self.log_info(_("Checking downloaded file..."))

        if self.captcha.task and not self.last_download:
            self.retry_captcha()

        elif self.check_file({'Empty file': re.compile(r'\A((.|)(\2|\s)*)\Z')},
                             delete=True):
            self.error(_("Empty file"))

        elif self.get_config('chk_filesize', False) and self.info.get('size'):
            # 10485760 is 10MB, tolerance is used when comparing displayed size on the hoster website to real size
            # For example displayed size can be 1.46GB for example, but real size can be 1.4649853GB
            self.check_filesize(self.info['size'], size_tolerance=10485760)

        else:
            self.log_info(_("File is OK"))


    def check_traffic(self):
        if not self.account:
            return True

        traffic = self.account.get_data('trafficleft')

        if traffic is None:
            return False

        elif traffic is -1:
            return True

        else:
            #@TODO: Rewrite in 0.4.10
            size = self.pyfile.size / 1024
            self.log_info(_("Filesize: %s KiB") % size,
                          _("Traffic left for user `%s`: %d KiB") % (self.account.user, traffic))
            return size <= traffic


    def check_filedupe(self):
        """
        Checks if same file was/is downloaded within same package

        :param starting: indicates that the current download is going to start
        :raises Skip:
        """
        pack = self.pyfile.package()

        for pyfile in self.pyload.files.cache.values():
            if pyfile is self.pyfile:
                continue

            if pyfile.name != self.pyfile.name or pyfile.package().folder != pack.folder:
                continue

            if pyfile.status in (0, 5, 7, 12):  #: (finished, waiting, starting, downloading)
                self.skip(pyfile.pluginname)

        dl_folder      = self.pyload.config.get("general", "download_folder")
        package_folder = pack.folder if self.pyload.config.get("general", "folder_per_package") else ""
        dl_location    = fs_join(dl_folder, package_folder, self.pyfile.name)

        if not exists(dl_location):
            return

        pyfile = self.pyload.db.findDuplicates(self.pyfile.id, package_folder, self.pyfile.name)
        if pyfile:
            self.skip(pyfile[0])

        size = os.stat(dl_location).st_size
        if size >= self.pyfile.size:
            self.skip(_("File exists"))


    #: Deprecated method, use `check_filedupe` instead (Remove in 0.4.10)
    def checkForSameFiles(self, *args, **kwargs):
        if self.pyload.config.get("download", "skip_existing"):
            return self.check_filedupe()
