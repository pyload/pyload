# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from builtins import _, map

import send2trash

from pyload.plugins.internal.addon import Addon
from pyload.plugins.utils import Expose, encode, exists, threaded


class AntiVirus(Addon):
    __name__ = "AntiVirus"
    __type__ = "addon"
    __version__ = "0.21"
    __status__ = "broken"

    __pyload_version__ = "0.5"

    # TODO: add trash option (use Send2Trash lib)
    __config__ = [
        ("enabled", "bool", "Activated", False),
        (
            "action",
            "Antivirus default;Delete;Quarantine",
            "Manage infected files",
            "Antivirus default",
        ),
        ("quardir", "folder", "Quarantine folder", ""),
        ("deltotrash", "bool", "Move to trash instead delete", True),
        ("scanfailed", "bool", "Scan failed downloads", False),
        ("avfile", "file", "Antivirus executable", ""),
        ("avargs", "str", "Executable arguments", ""),
        ("avtarget", "file;folder", "Scan target", "file"),
        ("ignore-err", "bool", "Ignore scan errors", False),
    ]

    __description__ = """Scan downloaded files with antivirus program"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    @Expose
    @threaded
    def scan(self, pyfile, thread):
        avfile = encode(self.config.get("avfile"))
        avargs = encode(self.config.get("avargs").strip())

        if not os.path.isfile(avfile):
            self.fail(self._("Antivirus executable not found"))

        scanfolder = self.config.get("avtarget") == "folder"

        if scanfolder:
            dl_folder = self.pyload.config.get("general", "download_folder")
            package_folder = (
                pyfile.package().folder
                if self.pyload.config.get("general", "folder_per_package")
                else ""
            )
            target = os.path.join(dl_folder, package_folder, pyfile.name)
            target_repr = "Folder: " + package_folder or dl_folder
        else:
            target = encode(pyfile.plugin.last_download)
            target_repr = "File: " + os.path.basename(pyfile.plugin.last_download)

        if not exists(target):
            return

        thread.addActive(pyfile)
        pyfile.setCustomStatus(self._("virus scanning"))
        pyfile.setProgress(0)

        try:
            p = subprocess.Popen(
                [avfile, avargs, target],
                bufsize=-1,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            out, err = list(map(str.strip, p.communicate()))

            if out:
                self.log_info(target_repr, out)

            if err:
                self.log_warning(target_repr, err)
                if not self.config.get("ignore-err"):
                    self.log_debug("Delete/Quarantine task aborted due scan error")
                    return

            if p.returncode:
                action = self.config.get("action")

                if scanfolder:
                    if action == "Antivirus default":
                        self.log_warning(
                            self._("Delete/Quarantine task skipped in folder scan mode")
                        )
                    return

                pyfile.error = self._("Infected file")

                try:
                    if action == "Delete":
                        if not self.config.get("deltotrash"):
                            os.remove(target)

                        else:
                            try:
                                send2trash.send2trash(target)

                            except NameError:
                                self.log_warning(
                                    self._(
                                        "Send2Trash lib not found, moving to quarantine instead"
                                    )
                                )
                                pyfile.setCustomStatus(self._("file moving"))
                                shutil.move(target, self.config.get("quardir"))

                            except Exception as e:
                                self.log_warning(
                                    self._(
                                        "Unable to move file to trash: {}, moving to quarantine instead"
                                    )
                                    % e
                                )
                                pyfile.setCustomStatus(self._("file moving"))
                                shutil.move(target, self.config.get("quardir"))

                            else:
                                self.log_debug("Successfully moved file to trash")

                    elif action == "Quarantine":
                        pyfile.setCustomStatus(self._("file moving"))
                        shutil.move(target, self.config.get("quardir"))

                except (IOError, shutil.Error) as e:
                    self.log_error(target_repr, action + " action failed!", e)

            elif not err:
                self.log_debug(target_repr, "No infected file found")

        finally:
            pyfile.setProgress(100)
            thread.finishFile(pyfile)

    def download_finished(self, pyfile):
        return self.scan(pyfile)

    def download_failed(self, pyfile):
        #: Check if pyfile is still "failed", maybe might has been restarted in meantime
        if pyfile.status == 8 and self.config.get("scanfailed"):
            return self.scan(pyfile)
