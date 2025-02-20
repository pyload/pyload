# -*- coding: utf-8 -*-

import mimetypes
import os
import re

from pyload.core.network.exceptions import Fail
from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils import format, parse
from pyload.core.utils.old import safejoin

from ..helpers import exists
from .hoster import BaseHoster


class BaseDownloader(BaseHoster):
    __name__ = "BaseDownloader"
    __type__ = "downloader"
    __version__ = "0.84"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
    ]

    __description__ = """Base downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    @property
    def last_download(self):
        return self._last_download if exists(self._last_download) else ""

    @last_download.setter
    def last_download(self, value):
        if isinstance(value, str) and exists(value):
            self._last_download = value

        else:
            self._last_download = ""

    def init_base(self):
        #: Enable simultaneous processing of multiple downloads
        self.limit_dl = 0

        #: Download chunks limit
        self.chunk_limit = None

        #: Enable download resuming if the hoster supports resuming
        self.resume_download = False

        #: Location where the last call to download was saved
        self._last_download = ""

        #: Re match of the last call to `check_download`
        self.last_check = None

        #: Restart flag
        self.restart_free = False  # TODO: Recheck in 0.6.x

        #: Download is possible with premium account only, don't fallback to free download
        self.no_fallback = False

    def setup_base(self):
        self._last_download = ""
        self.last_check = None
        self.restart_free = False
        self.no_fallback = False

        if self.account:
            self.chunk_limit = -1  #: -1 for unlimited
            self.resume_download = True
        else:
            self.chunk_limit = 1
            self.resume_download = False

    def load_account(self):
        if self.restart_free:
            self.account = False
        else:
            super().load_account()
            # self.restart_free = False

    def _process(self, thread):
        self.thread = thread

        try:
            self._initialize()
            self._setup()

            # TODO: Enable in 0.6.x
            # self.pyload.addon_manager.download_preparing(self.pyfile)
            # self.check_status()
            self.check_duplicates()

            self.pyfile.set_status("starting")

            try:
                self.log_info(self._("Processing url: ") + self.pyfile.url)
                self.process(self.pyfile)
                self.check_status()

                self._check_download()

            except Fail as exc:  # TODO: Move to DownloadThread in 0.6.x
                self.log_warning(
                    self._("Premium download failed")
                    if self.premium
                    else self._("Free download failed"),
                    str(exc),
                )
                if (
                    not self.no_fallback
                    and self.config.get("fallback", True)
                    and self.premium
                ):
                    self.restart(premium=False)

                else:
                    raise

        finally:
            self._finalize()

    # TODO: Remove in 0.6.x
    def _finalize(self):
        pypack = self.pyfile.package()

        self.pyload.addon_manager.dispatch_event("download_processed", self.pyfile)

        try:
            unfinished = any(
                fdata.get("status") in (3, 7)
                for fid, fdata in pypack.get_children().items()
                if fid != self.pyfile.id
            )
            if unfinished:
                return

            self.pyload.addon_manager.dispatch_event("package_processed", pypack)

            failed = any(
                fdata.get("status") in (1, 6, 8, 9, 14)
                for fid, fdata in pypack.get_children().items()
            )

            if not failed:
                return

            self.pyload.addon_manager.dispatch_event("package_failed", pypack)

        finally:
            self.check_status()

    def isresource(self, url, redirect=True, resumable=None):
        resource = False

        if resumable is None:
            resumable = self.resume_download

        if type(redirect) == int:
            maxredirs = max(redirect, 1)

        elif redirect:
            maxredirs = (
                self.config.get("maxredirs", default=5, plugin="UserAgentSwitcher")
            )

        else:
            maxredirs = 1

        header = self.load(url, just_header=True, redirect=False)

        for i in range(1, maxredirs):
            if not redirect or header.get("connection") == "close":
                resumable = False

            if "content-disposition" in header:
                resource = url

            elif header.get("location"):
                location = self.fixurl(header.get("location"), url)
                code = header.get("code")

                if code in (301, 302) or resumable:
                    self.log_debug(f"Redirect #{i} to: {location}")
                    header = self.load(location, just_header=True, redirect=False)
                    url = location
                    continue

            else:
                contenttype = header.get("content-type")
                extension = os.path.splitext(parse.name(url))[-1]

                if contenttype:
                    mimetype = contenttype.split(";")[0].strip()

                elif extension:
                    mimetype = (
                        mimetypes.guess_type(extension, False)[0]
                        or "application/octet-stream"
                    )

                else:
                    mimetype = None

                if mimetype and (resource or "html" not in mimetype):
                    resource = url
                else:
                    resource = False

            return resource

    def _on_notification(self, notification):
        if "progress" in notification:
            self.pyfile.set_progress(notification["progress"])

        if "disposition" in notification:
            self.pyfile.set_name(notification["disposition"])

    def _download(
        self, url, filename, get, post, ref, cookies, disposition, resume, chunks
    ):
        # TODO: Safe-filename check in HTTPDownload in 0.6.x
        filename = os.fsdecode(filename)
        resume = self.resume_download if resume is None else bool(resume)

        dl_chunks = self.pyload.config.get("download", "chunks")
        chunk_limit = chunks or self.chunk_limit or -1

        if -1 in (dl_chunks, chunk_limit):
            chunks = max(dl_chunks, chunk_limit)
        else:
            chunks = min(dl_chunks, chunk_limit)

        try:
            newname = self.req.http_download(
                url,
                filename,
                size=self.pyfile.size,
                get=get,
                post=post,
                ref=ref,
                cookies=cookies,
                chunks=chunks,
                resume=resume,
                status_notify=self._on_notification,
                disposition=disposition,
            )

        except IOError as exc:
            self.log_error(str(exc))
            self.fail(self._("IOError {}").format(exc.errno))

        except BadHeader as exc:
            self.req.http.code = exc.code
            raise

        else:
            if self.req.code in (404, 410):
                if newname:
                    bad_file = os.path.join(os.path.dirname(filename), newname)
                else:
                    bad_file = filename
                self.remove(bad_file)
                return ""
            else:
                self.log_info(self._("File saved"))

            return newname

        finally:
            self.pyfile.size = self.req.size
            self.captcha.correct()

    def download(
        self,
        url,
        get={},
        post={},
        ref=True,
        cookies=True,
        disposition=True,
        resume=None,
        chunks=None,
    ):
        """
        Downloads the content at url to download folder.

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
            self.log_debug(
                "DOWNLOAD URL " + url,
                *[
                    "{}={}".format(key, value)
                    for key, value in locals().items()
                    if key not in ("self", "url", "_[1]")
                ],
            )

        dl_basename = parse.name(self.pyfile.name)
        self.pyfile.name = dl_basename

        self.check_duplicates()

        self.pyfile.set_status("downloading")

        dl_url = self.fixurl(url)

        dl_folder = self.pyload.config.get("general", "storage_folder")
        dl_dirname = safejoin(dl_folder, self.pyfile.package().folder)
        dl_filename = safejoin(dl_dirname, self.pyfile.name)

        os.makedirs(dl_dirname, exist_ok=True)
        self.set_permissions(dl_dirname)

        self.pyload.addon_manager.dispatch_event(
            "download_start", self.pyfile, dl_url, dl_filename
        )
        self.check_status()

        newname = self._download(
            dl_url, dl_filename, get, post, ref, cookies, disposition, resume, chunks
        )

        if disposition and newname:
            self.pyfile.name = newname
            dl_filename = safejoin(dl_dirname, newname)

        self.set_permissions(dl_filename)

        self.last_download = dl_filename

        return dl_filename

    def scan_download(self, rules, read_size=1_048_576):
        """
        Checks the content of the last downloaded file, re match is saved to
        `last_check`

        :param rules: dict with names and rules to match (compiled regexp or strings)
        :param read_size: size to read and scan
        :return: dictionary key of the first rule that matched
        """
        if not self.last_download:
            self.log_warning(self._("No file to scan"))
            return

        dl_file = os.fsdecode(self.last_download)  # TODO: Recheck in 0.6.x
        with open(dl_file, mode="rb") as fp:
            content = fp.read(read_size)

        for name, rule in rules.items():
            if isinstance(rule, bytes):
                if rule in content:
                    return name

            elif isinstance(rule, str):
                raise TypeError(f"Cannot check binary data with string rule '{name}'")

            elif hasattr(rule, "search"):
                m = rule.search(content)
                if m is not None:
                    self.last_check = m
                    return name

            elif callable(rule):
                return rule(content)

    def _check_download(self):
        def _is_empty_file(content):
            firstbyte = content[0:1]
            whitespaces_count = len(re.findall(rb"[%s\s]" % firstbyte, content))
            return whitespaces_count == len(content)

        self.log_info(self._("Checking download..."))
        self.pyfile.set_custom_status(self._("checking"))

        if not self.last_download:
            if self.captcha.task:
                self.retry_captcha()
            else:
                self.error(self._("No file downloaded"))

        elif self.scan_download({"Empty file": _is_empty_file}):
            if self.remove(self.last_download):
                self.last_download = ""
            self.error(self._("Empty file"))

        else:
            self.pyload.addon_manager.dispatch_event("download_check", self.pyfile)
            self.check_status()

        self.log_info(self._("File is OK"))

    def out_of_traffic(self):
        if not self.account:
            return False

        traffic = self.account.get_data("trafficleft")

        if traffic is None:
            return True

        elif traffic == -1:
            return False

        else:
            size = self.pyfile.size
            self.log_info(
                self._("Filesize: {}").format(format.size(size)),
                self._("Traffic left for user `{}`: {}").format(
                    self.account.user, format.size(traffic)
                ),
            )
            return size > traffic

    # def check_size(self, file_size, size_tolerance=1 << 10, delete=False):
    # """
    # Checks the file size of the last downloaded file

    # :param file_size: expected file size
    # :param size_tolerance: size check tolerance
    # """
    # self.log_info(self._("Checking file size..."))

    # if not self.last_download:
    # self.log_warning(self._("No file to check"))
    # return

    # dl_file = encode(self.last_download)
    # dl_size = os.stat(dl_file).st_size

    # try:
    # if dl_size == 0:
    # delete = True
    # self.fail(self._("Empty file"))

    # elif file_size > 0:
    # diff = abs(file_size - dl_size)

    # if diff > size_tolerance:
    # self.fail(self._("File size mismatch | Expected file size: {} bytes | Downloaded file size: {} bytes").format((file_size), dl_size))

    # elif diff != 0:
    # self.log_warning(self._("File size is not equal to expected download size, but does not exceed the tolerance threshold"))
    # self.log_debug(f"Expected file size: {file_size} bytes"
    # "Downloaded file size: {} bytes".format(dl_size)
    # "Tolerance threshold: {} bytes".format(size_tolerance))
    # else:
    # delete = False
    # self.log_info(self._("File size match"))

    # finally:
    # if delete:
    # self.remove(dl_file, try_trash=False)

    def check_duplicates(self):
        """
        Checks if same file was downloaded within same package.

        :raises Skip:
        """
        pack_folder = self.pyfile.package().folder

        for pyfile in list(self.pyload.files.cache.values()):
            if (
                pyfile != self.pyfile
                and pyfile.name == self.pyfile.name
                and pyfile.package().folder == pack_folder
            ):
                if pyfile.status in (
                    0,
                    12,
                    5,
                    7,
                ):  #: finished / downloading / waiting / starting
                    self.skip(pyfile.pluginname)

        dl_folder = self.pyload.config.get("general", "storage_folder")
        dl_file = os.path.join(dl_folder, pack_folder, self.pyfile.name)

        if not exists(dl_file):
            return

        if os.stat(dl_file).st_size == 0:
            if self.remove(self.last_download):
                self.last_download = ""
            return

        if self.pyload.config.get("download", "skip_existing"):
            plugin = self.pyload.db.find_duplicates(
                self.pyfile.id, pack_folder, self.pyfile.name
            )
            msg = plugin[0] if plugin else self._("File exists")
            self.skip(msg)

        else:
            # Same file exists but, it does not belong to our pack, add a trailing
            # counter
            name, ext = os.path.splitext(self.pyfile.name)
            m = re.match(r"(.+?)(?:\((\d+)\))?$", name)
            dl_n = int(m.group(2) or "0")

            while True:
                name = "{} ({}){}".format(m.group(1), dl_n + 1, ext)
                dl_file = os.path.join(dl_folder, pack_folder, name)
                if not exists(dl_file):
                    break

                dl_n += 1

            self.pyfile.name = name

    #: Deprecated method (Recheck in 0.6.x)
    def check_for_same_files(self, *args, **kwargs):
        pass
