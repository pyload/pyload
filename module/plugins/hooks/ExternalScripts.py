# -*- coding: utf-8 -*-

import os
import subprocess

from ..internal.Addon import Addon
from ..internal.misc import Expose, encode


class ExternalScripts(Addon):
    __name__ = "ExternalScripts"
    __type__ = "hook"
    __version__ = "0.73"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", True),
                  ("unlock", "bool", "Execute script concurrently", False)]

    __description__ = """Run external scripts"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    def init(self):
        self.scripts = {}

        self.folders = ["pyload_start", "pyload_restart", "pyload_stop",
                        "before_reconnect", "after_reconnect",
                        "download_preparing", "download_failed",
                        # @TODO: Invert 'download_processed', 'download_finished' order in 0.4.10
                        "download_finished", "download_processed",
                        "archive_extract_failed", "archive_extracted",
                        # @TODO: Invert 'package_finished', 'package_processed' order in 0.4.10
                        "package_finished", "package_processed",
                        "package_deleted", "package_failed", "package_extract_failed", "package_extracted",
                        # @TODO: Invert `all_downloads_processed`, `all_downloads_finished` order in 0.4.10
                        "all_downloads_processed", "all_downloads_finished",
                        "all_archives_extracted", "all_archives_processed"]

        self.event_map = {'archive_extract_failed': "archive_extract_failed",
                          'archive_extracted': "archive_extracted",
                          'package_extract_failed': "package_extract_failed",
                          'package_extracted': "package_extracted",
                          'all_archives_extracted': "all_archives_extracted",
                          'all_archives_processed': "all_archives_processed",
                          'pyload_updated': "pyload_updated"}

        self.periodical.start(60)
        self.periodical_task()  # @NOTE: Initial scan so dont miss `pyload_start` scripts if any

    def activate(self):
        self.pyload_start()

    def make_folders(self):
        for folder in self.folders:
            dir = os.path.join("scripts", folder)

            if os.path.isdir(dir):
                continue

            try:
                os.makedirs(dir)

            except OSError, e:
                self.log_debug(e, trace=True)

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

                    if file[0] in ("#", "_") or file.endswith(
                            "~") or file.endswith(".swp"):
                        continue

                    if not os.access(file, os.X_OK):
                        self.log_warning(
                            _("Script `%s` is not executable") % entry)

                    scripts.append(file)

            new_scripts = [
                _s for _s in scripts if _s not in self.scripts[folder]]

            if new_scripts:
                script_names = map(os.path.basename, new_scripts)
                self.log_info(_("Activated scripts in folder `%s`: %s")
                              % (folder, ", ".join(script_names)))

            removed_scripts = [
                _s for _s in self.scripts[folder] if _s not in scripts]

            if removed_scripts:
                script_names = map(os.path.basename, removed_scripts)
                self.log_info(_("Deactivated scripts in folder `%s`: %s")
                              % (folder, ", ".join(script_names)))

            self.scripts[folder] = scripts

    def call_cmd(self, command, *args, **kwargs):
        call = map(encode, [command] + list(args))

        self.log_debug(
            "EXECUTE " + " ".join('"' + _arg + '"' if ' ' in _arg else _arg for _arg in call))

        p = subprocess.Popen(call, bufsize=-1)  # @NOTE: output goes to pyload

        return p

    @Expose
    def call_script(self, folder, *args, **kwargs):
        scripts = self.scripts.get(folder)

        if folder not in self.scripts:
            self.log_debug("Folder `%s` not found" % folder)
            return

        if not scripts:
            self.log_debug("No script found under folder `%s`" % folder)
            return

        self.log_info(_("Executing scripts in folder `%s`...") % folder)

        for file in scripts:
            try:
                p = self.call_cmd(file, *args)

            except Exception, e:
                self.log_error(_("Runtime error: %s") % file,
                               e or _("Unknown error"))

            else:
                lock = kwargs.get('lock', None)
                if lock is True or lock is None and not self.config.get(
                        'unlock'):
                    p.communicate()

    def pyload_updated(self, etag):
        self.call_script("pyload_updated", etag)

    def pyload_start(self):
        self.call_script('pyload_start')

    def exit(self):
        event = "restart" if self.pyload.do_restart else "stop"
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
        args = [
            pyfile.id,
            pyfile.name,
            archive.filename,
            archive.out,
            archive.files]
        self.call_script("archive_extract_failed", *args)

    def archive_extracted(self, pyfile, archive):
        args = [
            pyfile.id,
            pyfile.name,
            archive.filename,
            archive.out,
            archive.files]
        self.call_script("archive_extracted", *args)

    def package_finished(self, pypack):
        dl_folder = self.pyload.config.get("general", "download_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_finished", *args)

    def package_processed(self, pypack):
        dl_folder = self.pyload.config.get("general", "download_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_processed", *args)

    def package_deleted(self, pid):
        dl_folder = self.pyload.config.get("general", "download_folder")
        pdata = self.pyload.api.getPackageInfo(pid)

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pdata.folder)

        args = [pdata.pid, pdata.name, dl_folder, pdata.password]
        self.call_script("package_deleted", *args)

    def package_failed(self, pypack):
        dl_folder = self.pyload.config.get("general", "download_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_failed", *args)

    def package_extract_failed(self, pypack):
        dl_folder = self.pyload.config.get("general", "download_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pypack.folder)

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_extract_failed", *args)

    def package_extracted(self, pypack):
        dl_folder = self.pyload.config.get("general", "download_folder")

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
