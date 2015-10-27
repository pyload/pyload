# -*- coding: utf-8 -*-

import os
import subprocess

from module.plugins.internal.Addon import Addon, Expose
from module.plugins.internal.utils import encode, fs_join


class ExternalScripts(Addon):
    __name__    = "ExternalScripts"
    __type__    = "hook"
    __version__ = "0.55"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated"                   , True ),
                  ("lock"     , "bool", "Wait for script to terminate", False)]

    __description__ = """Run external scripts"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        self.scripts = {}

        self.event_map = {'allDownloadsFinished'  : "all_downloads_finished" ,
                          'allDownloadsProcessed' : "all_downloads_processed",
                          'packageDeleted'        : "package_deleted"        ,
                          'archive_extract_failed': "archive_extract_failed" ,
                          'archive_extracted'     : "archive_extracted"      ,
                          'package_extract_failed': "package_extract_failed" ,
                          'package_extracted'     : "package_extracted"      ,
                          'all_archives_extracted': "all_archives_extracted" ,
                          'all_archives_processed': "all_archives_processed" }

        folders = ["pyload_start", "pyload_restart", "pyload_stop",
                   "before_reconnect", "after_reconnect",
                   "download_preparing", "download_failed", "download_finished",
                   "archive_extract_failed", "archive_extracted",
                   "package_finished", "package_deleted", "package_extract_failed", "package_extracted",
                   "all_downloads_processed", "all_downloads_finished",  #@TODO: Invert `all_downloads_processed`, `all_downloads_finished` order in 0.4.10
                   "all_archives_extracted", "all_archives_processed"]

        for folder in folders:
            path = os.path.join("scripts", folder)
            self.init_folder(folder, path)

        for folder, scripts in self.scripts.items():
            if scripts:
                self.log_info(_("Installed scripts in folder `%s`: %s")
                              % (folder, ", ".join(scripts)))

        self.pyload_start()


    def init_folder(self, name, path):
        self.scripts[name] = []

        if not os.path.isdir(path):
            try:
                os.makedirs(path)

            except OSError, e:
                self.log_debug(e)
                return

        for filename in os.listdir(path):
            file = fs_join(path, filename)
            if not os.path.isfile(file):
                continue

            if file[0] in ("#", "_") or file.endswith("~") or file.endswith(".swp"):
                continue

            if not os.access(file, os.X_OK):
                self.log_warning(_("Script not executable: [%s] %s") % (name, file))

            self.scripts[name].append(file)
            self.log_info(_("Registered script: [%s] %s") % (name, file))


    @Expose
    def call(self, script, args=[], lock=None):
        if lock is None:
            lock = self.get_config('lock')

        try:
            script = os.path.abspath(script)
            args   = [script] + map(lambda arg: encode(arg) if isinstance(arg, basestring) else encode(str(arg)), args)

            self.log_info(_("EXECUTE [%s] %s") % (os.path.dirname(script), args))
            p = subprocess.Popen(args, bufsize=-1)  #@NOTE: output goes to pyload
            if lock:
                p.communicate()

        except Exception, e:
            self.log_error(_("Runtime error: %s") % script,
                           e or _("Unknown error"))


    def _call(self, folder, args=[], lock=None):
        for script in self.scripts[folder]:
            self.call(script, args, lock)


    def pyload_start(self):
        self._call('pyload_start')


    def exit(self):
        folder = "pyload_restart" if self.pyload.do_restart else "pyload_stop"
        self._call(folder, lock=True)


    def before_reconnect(self, ip):
        args = [ip]
        self._call("before_reconnect", args)


    def after_reconnect(self, ip, oldip):
        args = [ip, oldip]
        self._call("after_reconnect", args)


    def download_preparing(self, pyfile):
        args = [pyfile.id, pyfile.name, None, pyfile.pluginname, pyfile.url]
        self._call("download_preparing", args)


    def download_failed(self, pyfile):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fs_join(self.pyload.config.get("general", "download_folder"), pyfile.package().folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        file = fs_join(dl_folder, pyfile.name)
        args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
        self._call("download_failed", args)


    def download_finished(self, pyfile):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fs_join(self.pyload.config.get("general", "download_folder"), pyfile.package().folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        file = fs_join(dl_folder, pyfile.name)
        args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
        self._call("download_finished", args)


    def archive_extract_failed(self, pyfile, archive):
        args = [pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
        self._call("archive_extract_failed", args)


    def archive_extracted(self, pyfile, archive):
        args = [pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
        self._call("archive_extracted", args)


    def package_finished(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self._call("package_finished", args)


    def package_deleted(self, pid):
        pdata = self.pyload.api.getPackageInfo(pid)

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fs_join(self.pyload.config.get("general", "download_folder"), pdata.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        args = [pdata.pid, pdata.name, dl_folder, pdata.password]
        self._call("package_deleted", args)


    def package_extract_failed(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self._call("package_extract_failed", args)


    def package_extracted(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        args = [pypack.id, pypack.name, dl_folder]
        self._call("package_extracted", args)


    def all_downloads_finished(self):
        self._call("all_downloads_finished")


    def all_downloads_processed(self):
        self._call("all_downloads_processed")


    def all_archives_extracted(self):
        self._call("all_archives_extracted")


    def all_archives_processed(self):
        self._call("all_archives_processed")
