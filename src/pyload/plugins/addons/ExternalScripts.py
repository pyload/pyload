# -*- coding: utf-8 -*-

import os
import subprocess

from ..base.addon import BaseAddon, expose


class ExternalScripts(BaseAddon):
    __name__ = "ExternalScripts"
    __type__ = "addon"
    __version__ = "0.73"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("unlock", "bool", "Execute script concurrently", False),
    ]

    __description__ = """Run external scripts"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com"),
    ]

    def init(self):
        self.scripts = {}

        self.folders = [
            "pyload_start",
            "pyload_restart",
            "pyload_stop",
            "before_reconnect",
            "after_reconnect",
            "download_preparing",
            "download_failed",
            # TODO: Invert 'download_processed', 'download_finished' order
            # in 0.6.x
            "download_finished",
            "download_processed",
            "archive_extract_failed",
            "archive_extracted",
            # TODO: Invert 'package_finished', 'package_processed' order in
            # 0.6.x
            "package_finished",
            "package_processed",
            "package_deleted",
            "package_failed",
            "package_extract_failed",
            "package_extracted",
            # TODO: Invert `all_downloads_processed`,
            # `all_downloads_finished` order in 0.6.x
            "all_downloads_processed",
            "all_downloads_finished",
            "all_archives_extracted",
            "all_archives_processed",
        ]

        self.event_map = {
            "archive_extract_failed": "archive_extract_failed",
            "archive_extracted": "archive_extracted",
            "package_extract_failed": "package_extract_failed",
            "package_extracted": "package_extracted",
            "all_archives_extracted": "all_archives_extracted",
            "all_archives_processed": "all_archives_processed",
            "pyload_updated": "pyload_updated",
        }

        self.periodical.start(60)
        self.periodical_task()  # NOTE: Initial scan so dont miss `pyload_start` scripts if any

    def activate(self):
        self.pyload_start()

    def make_folders(self):
        for folder in self.folders:
            dir = os.path.join(self.pyload.userdir, "scripts", folder)

            if os.path.isdir(dir):
                continue

            os.makedirs(dir, exist_ok=True)

    def periodical_task(self):
        self.make_folders()

        for folder in self.folders:
            scripts = []
            dirname = os.path.join("scripts", folder)

            if folder not in self.scripts:
                self.scripts[folder] = []

            if os.path.isdir(dirname):
                for entry in os.listdir(dirname):
                    file = os.path.join(dirname, entry)

                    if not os.path.isfile(file):
                        continue

                    if (
                        file[0] in ("#", "_")
                        or file.endswith("~")
                        or file.endswith(".swp")
                    ):
                        continue

                    if not os.access(file, os.X_OK):
                        self.log_warning(
                            self._("Script `{}` is not executable").format(entry)
                        )

                    scripts.append(file)

            new_scripts = [s for s in scripts if s not in self.scripts[folder]]

            if new_scripts:
                self.log_info(
                    self._("Activated scripts in folder `{}`: {}").format(
                        folder, ", ".join(os.path.basename(x) for x in new_scripts)
                    )
                )

            removed_scripts = [s for s in self.scripts[folder] if s not in scripts]

            if removed_scripts:
                self.log_info(
                    self._("Deactivated scripts in folder `{}`: {}").format(
                        folder, ", ".join(os.path.basename(x) for x in removed_scripts)
                    )
                )

            self.scripts[folder] = scripts

    def call_cmd(self, command, *args, **kwargs):
        call = (str(cmd) for cmd in [command] + list(args))

        self.log_debug(
            "EXECUTE "
            + " ".join('"' + arg + '"' if " " in arg else arg for arg in call)
        )

        p = subprocess.Popen(call, bufsize=-1)  # NOTE: output goes to pyload

        return p

    @expose
    def call_script(self, folder, *args, **kwargs):
        scripts = self.scripts.get(folder)

        if folder not in self.scripts:
            self.log_debug(f"Folder `{folder}` not found")
            return

        if not scripts:
            self.log_debug(f"No script found under folder `{folder}`")
            return

        self.log_info(self._("Executing scripts in folder `{}`...").format(folder))

        for file in scripts:
            try:
                p = self.call_cmd(file, *args)

            except Exception as exc:
                self.log_error(
                    self._("Runtime error: {}").format(file),
                    exc or self._("Unknown error"),
                )

            else:
                lock = kwargs.get("lock", None)
                if lock is not False and not self.config.get("unlock"):
                    p.communicate()

    def pyload_updated(self, etag):
        self.call_script("pyload_updated", etag)

    def pyload_start(self):
        self.call_script("pyload_start")

    def exit(self):
        event = "restart" if self.pyload._do_restart else "stop"
        self.call_script("pyload_" + event, lock=True)

    def before_reconnect(self, ip):
        self.call_script("before_reconnect", ip)

    def after_reconnect(self, ip, oldip):
        self.call_script("after_reconnect", ip, oldip)

    def download_preparing(self, pyfile):
        args = [pyfile.id, pyfile.name, None, pyfile.pluginname, pyfile.url]
        self.call_script("download_preparing", *args)

    def download_failed(self, pyfile):
        file = pyfile.plugin.last_download
        args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
        self.call_script("download_failed", *args)

    def download_finished(self, pyfile):
        file = pyfile.plugin.last_download
        args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
        self.call_script("download_finished", *args)

    def download_processed(self, pyfile):
        file = pyfile.plugin.last_download
        args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
        self.call_script("download_processed", *args)

    def archive_extract_failed(self, pyfile, archive):
        args = [pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
        self.call_script("archive_extract_failed", *args)

    def archive_extracted(self, pyfile, archive):
        args = [pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
        self.call_script("archive_extracted", *args)

    def package_finished(self, pypack):
        dl_folder = self.pyload.config.get("general", "storage_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_finished", *args)

    def package_processed(self, pypack):
        dl_folder = self.pyload.config.get("general", "storage_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_processed", *args)

    def package_deleted(self, pid):
        dl_folder = self.pyload.config.get("general", "storage_folder")
        pdata = self.pyload.api.get_package_info(pid)

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pdata.folder)

        args = [pdata.pid, pdata.name, dl_folder, pdata.password]
        self.call_script("package_deleted", *args)

    def package_failed(self, pypack):
        dl_folder = self.pyload.config.get("general", "storage_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_failed", *args)

    def package_extract_failed(self, pypack):
        dl_folder = self.pyload.config.get("general", "storage_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_extract_failed", *args)

    def package_extracted(self, pypack):
        dl_folder = self.pyload.config.get("general", "storage_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder]
        self.call_script("package_extracted", *args)

    def all_downloads_finished(self):
        self.call_script("all_downloads_finished")

    def all_downloads_processed(self):
        self.call_script("all_downloads_processed")

    def all_archives_extracted(self):
        self.call_script("all_archives_extracted")

    def all_archives_processed(self):
        self.call_script("all_archives_processed")
