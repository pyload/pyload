# -*- coding: utf-8 -*-
import hashlib
import os
import re
import time
import zlib
from threading import Event

from pyload.core.utils import format

from ..base.addon import BaseAddon, threaded


def compute_checksum(local_file, algorithm, progress_notify=None, abort=None):
    file_size = os.stat(local_file).st_size
    processed = 0
    if progress_notify:
        progress_notify(0)

    try:
        if algorithm in getattr(
            hashlib,
            "algorithms",
            ("md5", "sha1", "sha224", "sha256", "sha384", "sha512"),
        ):
            h = getattr(hashlib, algorithm)()

            with open(local_file, mode="rb") as fp:
                for chunk in iter(lambda: fp.read(128 * h.block_size), ""):
                    if abort and abort():
                        return False

                    h.update(chunk)
                    processed += len(chunk)

                    if progress_notify:
                        progress_notify(processed * 100 // file_size)

            return h.hexdigest()

        elif algorithm in ("adler32", "crc32"):
            hf = getattr(zlib, algorithm)
            last = 0

            with open(local_file, mode="rb") as fp:
                for chunk in iter(lambda: fp.read(8192), ""):
                    if abort and abort():
                        return False

                    last = hf(chunk, last)
                    processed += len(chunk)

                    if progress_notify:
                        progress_notify(processed * 100 // file_size)

            #: zlib sometimes return negative value
            return "{:x}".format((2 ** 32 + last) & 0xFFFFFFFF)

        else:
            return None

    finally:
        if progress_notify:
            progress_notify(100)


class Checksum(BaseAddon):
    __name__ = "Checksum"
    __type__ = "addon"
    __version__ = "0.34"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        (
            "check_checksum",
            "bool",
            "Check checksum? (If False only size will be verified)",
            True,
        ),
        ("check_action", "fail;retry;nothing", "What to do if check fails?", "retry"),
        ("max_tries", "int", "Number of retries", 2),
        ("retry_action", "fail;nothing", "What to do if all retries fail?", "fail"),
        ("wait_time", "int", "Time to wait before each retry (seconds)", 1),
    ]

    __description__ = """Verify downloaded file size and checksum"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    _methodmap = {"sfv": "crc32", "crc": "crc32", "hash": "md5"}

    _regexmap = {
        "sfv": r"^(?P<NAME>[^;].+)\s+(?P<HASH>[0-9A-Fa-f]{8})$",
        "md5": r"^(?P<NAME>[0-9A-Fa-f]{32})  (?P<FILE>.+)$",
        "crc": r"filename=(?P<NAME>.+)\nsize=(?P<SIZE>\d+)\ncrc32=(?P<HASH>[0-9A-Fa-f]{8})$",
        "default": r"^(?P<HASH>[0-9A-Fa-f]+)\s+\*?(?P<NAME>.+)$",
    }

    def activate(self):
        if not self.config.get("check_checksum"):
            self.log_info(
                self._("Checksum validation is disabled in plugin configuration")
            )

    def init(self):
        self.algorithms = sorted(
            getattr(
                hashlib,
                "algorithms",
                ("md5", "sha1", "sha224", "sha256", "sha384", "sha512"),
            ),
            reverse=True,
        )

        self.algorithms.extend(["crc32", "adler32"])

        self.formats = self.algorithms + ["sfv", "crc", "hash"]

        self.retries = {}

    def download_finished(self, pyfile):
        """
        Compute checksum for the downloaded file and compare it with the hash provided
        by the hoster.

        pyfile.plugin.check_data should be a dictionary which can
        contain: a) if known, the exact filesize in bytes (e.g. 'size':
        123456789) b) hexadecimal hash string with algorithm name as key
        (e.g. 'md5': "d76505d0869f9f928a17d42d66326307")
        """
        if hasattr(pyfile.plugin, "check_data") and isinstance(
            pyfile.plugin.check_data, dict
        ):
            data = pyfile.plugin.check_data.copy()

        elif hasattr(pyfile.plugin, "api_data") and isinstance(
            pyfile.plugin.api_data, dict
        ):
            data = pyfile.plugin.api_data.copy()

        elif hasattr(pyfile.plugin, "info") and isinstance(pyfile.plugin.info, dict):
            data = pyfile.plugin.info.copy()
            # NOTE: Don't check file size until a similary matcher will be implemented
            data.pop("size", None)

        else:
            return

        pyfile.set_status("processing")

        if not pyfile.plugin.last_download:
            self.check_failed(pyfile, None, "No file downloaded")

        local_file = os.fsdecode(pyfile.plugin.last_download)
        # dl_folder  = self.pyload.config.get("general", "storage_folder")
        # local_file = encode(os.path.join(dl_folder, pyfile.package().folder, pyfile.name))

        if not os.path.isfile(local_file):
            self.check_failed(pyfile, None, "File does not exist")

        #: Validate file size
        if "size" in data:
            api_size = int(data["size"])
            file_size = os.path.getsize(local_file)

            if api_size != file_size:
                self.log_warning(
                    self._("File {} has incorrect size: {} B ({} expected)").format(
                        pyfile.name, file_size, api_size
                    )
                )
                self.check_failed(pyfile, local_file, "Incorrect file size")

            data.pop("size", None)

        self.log_debug(data)
        #: Validate checksum
        if data and self.config.get("check_checksum"):
            data["hash"] = data.get("hash", {})

            for key in self.algorithms:
                if key in data and key not in data["hash"]:
                    data["hash"][key] = data[key]
                    break

            if len(data["hash"]) > 0:
                for key in self.algorithms:
                    if key in data["hash"]:
                        pyfile.set_custom_status(self._("checksum verifying"))
                        try:
                            checksum = compute_checksum(
                                local_file,
                                key.replace("-", "").lower(),
                                progress_notify=pyfile.set_progress,
                                abort=lambda: pyfile.abort,
                            )
                        finally:
                            pyfile.set_status("processing")

                        if checksum is False:
                            continue

                        elif checksum is not None:
                            if checksum.lower() == data["hash"][key].lower():
                                self.log_info(
                                    self._(
                                        'File integrity of "{}" verified by {} checksum ({})'
                                    ).format(pyfile.name, key.upper(), checksum.lower())
                                )
                                pyfile.error = self._("checksum verified")
                                break

                            else:
                                self.log_warning(
                                    self._(
                                        "{} checksum for file {} does not match ({} != {})"
                                    ).format(
                                        key.upper(),
                                        pyfile.name,
                                        checksum,
                                        data["hash"][key].lower(),
                                    )
                                )

                                self.check_failed(
                                    pyfile, local_file, "Checksums do not match"
                                )

                        else:
                            self.log_warning(
                                self._("Unsupported hashing algorithm"), key.upper()
                            )

                else:
                    self.log_warning(
                        self._('Unable to validate checksum for file: "{}"').format(
                            pyfile.name
                        )
                    )

    def check_failed(self, pyfile, local_file, msg):
        check_action = self.config.get("check_action")
        if check_action == "retry":
            max_tries = self.config.get("max_tries")
            retry_action = self.config.get("retry_action")
            if all(r < max_tries for _, r in pyfile.plugin.retries.items()):
                if local_file:
                    os.remove(local_file)

                pyfile.plugin.retry(max_tries, self.config.get("wait_time"), msg)

            elif retry_action == "nothing":
                return

        elif check_action == "nothing":
            return

        os.remove(local_file)
        pyfile.plugin.fail(msg)

    def package_finished(self, pypack):
        event_finished = Event()
        self.verify_package(pypack, event_finished)
        event_finished.wait()  #: Postpone `all_downloads_processed` event until we actually finish

    @threaded
    def verify_package(self, pypack, event_finished, thread=None):
        try:
            dl_folder = os.path.join(
                self.pyload.config.get("general", "storage_folder"), pypack.folder, ""
            )

            pdata = list(pypack.get_children().items())
            files_ids = {fdata["name"]: fdata["id"] for fid, fdata in pdata}
            failed_queue = []
            for fid, fdata in pdata:
                file_type = os.path.splitext(fdata["name"])[1][1:].lower()

                if file_type not in self.formats:
                    continue

                hash_file = os.fsdecode(os.path.join(dl_folder, fdata["name"]))
                if not os.path.isfile(hash_file):
                    self.log_warning(self._("File not found"), fdata["name"])
                    continue

                with open(hash_file) as fp:
                    text = fp.read()

                failed = []
                for m in re.finditer(
                    self._regexmap.get(file_type, self._regexmap["default"]), text, re.M
                ):
                    data = m.groupdict()
                    self.log_debug(fdata["name"], data)

                    local_file = os.fsdecode(os.path.join(dl_folder, data["NAME"]))
                    algorithm = self._methodmap.get(file_type, file_type)

                    pyfile = None
                    fid = files_ids.get(data["NAME"], None)
                    if fid is not None:
                        pyfile = self.pyload.files.get_file(fid)
                        pyfile.set_custom_status(self._("checksum verifying"))
                        thread.add_active(pyfile)
                        try:
                            checksum = compute_checksum(
                                local_file,
                                algorithm,
                                progress_notify=pyfile.set_progress,
                                abort=lambda: pyfile.abort,
                            )
                        finally:
                            thread.finish_file(pyfile)

                    else:
                        checksum = compute_checksum(local_file, algorithm)

                    if checksum is False:
                        continue

                    elif checksum is not None:
                        if checksum.lower() == data["HASH"].lower():
                            self.retries.pop(fid, 0)
                            self.log_info(
                                self._(
                                    'File integrity of "{}" verified by {} checksum ({})'
                                ).format(data["NAME"], algorithm, checksum)
                            )

                            if pyfile is not None:
                                pyfile.error = self._("checksum verified")
                                pyfile.set_status("finished")
                                pyfile.release()

                        else:
                            self.log_warning(
                                self._(
                                    "{} checksum for file {} does not match ({} != {})"
                                ).format(
                                    algorithm.upper(),
                                    data["NAME"],
                                    checksum.lower(),
                                    data["HASH"].lower(),
                                )
                            )

                            if fid is not None:
                                failed.append((fid, local_file))
                    else:
                        self.log_warning(
                            self._("Unsupported hashing algorithm"), algorithm.upper()
                        )

                if failed:
                    failed_queue.extend(failed)

                else:
                    self.log_info(
                        self._(
                            'All files specified by "{}" verified successfully'
                        ).format(fdata["name"])
                    )

            if failed_queue:
                self.package_check_failed(
                    failed_queue, thread, "Checksums do not match"
                )

        finally:
            event_finished.set()

    @threaded
    def package_check_failed(self, failed_queue, parent_thread, msg):
        parent_thread.join()  #: wait for calling thread to finish
        time.sleep(1)

        check_action = self.config.get("check_action")
        retry_action = self.config.get("retry_action")

        for fid, local_file in failed_queue:
            pyfile = self.pyload.files.get_file(fid)
            try:
                if check_action == "retry":
                    retry_count = self.retries.get(fid, 0)
                    max_tries = self.config.get("max_tries")
                    if retry_count < max_tries:
                        if local_file:
                            os.remove(local_file)

                        self.retries[fid] = retry_count + 1

                        wait_time = self.config.get("wait_time")
                        self.log_info(
                            self._("Waiting {}...").format(format.time(wait_time))
                        )
                        time.sleep(wait_time)

                        pyfile.package().set_finished = (
                            False  #: Force `package_finished` event again
                        )
                        self.pyload.files.restart_file(fid)
                        continue

                    else:
                        self.retries.pop(fid, 0)
                        if retry_action == "nothing":
                            continue

                else:
                    self.retries.pop(fid, 0)
                    if check_action == "nothing":
                        continue

                os.remove(local_file)

                pyfile.error = msg
                pyfile.set_status("failed")

            finally:
                pyfile.release()
