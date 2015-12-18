# -*- coding: utf-8 -*-

import os
import subprocess

from module.plugins.internal.Addon import Addon, Expose
from module.plugins.internal.misc import encode, fsjoin


class ExternalScripts(Addon):
    __name__    = "ExternalScripts"
    __type__    = "hook"
    __version__ = "0.60"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated"                  , True ),
                  ("unlock"   , "bool", "Execute script concurrently", False)]

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
                          'all_archives_processed': "all_archives_processed" ,
                          'pyload_updated'        : "pyload_updated"         }

        self.start_periodical(60)
        self.pyload_start()


    def make_folders(self):
        folders = ["pyload_start", "pyload_restart", "pyload_stop",
                   "before_reconnect", "after_reconnect",
                   "download_preparing", "download_failed", "download_finished",
                   "archive_extract_failed", "archive_extracted",
                   "package_finished", "package_deleted", "package_extract_failed", "package_extracted",
                   "all_downloads_processed", "all_downloads_finished",  #@TODO: Invert `all_downloads_processed`, `all_downloads_finished` order in 0.4.10
                   "all_archives_extracted", "all_archives_processed"]

        for folder in folders:
            dir = os.path.join("scripts", folder)

            if os.path.isdir(dir):
                continue

            try:
                os.makedirs(dir)

            except OSError, e:
                self.log_debug(e, trace=True)


    def periodical(self):
        self.make_folders()

        folders = [entry for entry in os.listdir("scripts") \
                   if os.path.isdir(os.path.join("scripts", entry))]

        for folder in folders:
            self.scripts[folder] = []

            dirname = os.path.join("scripts", folder)

            for entry in os.listdir(dirname):
                file = os.path.join(dirname, entry)

                if not os.path.isfile(file):
                    continue

                if file[0] in ("#", "_") or file.endswith("~") or file.endswith(".swp"):
                    continue

                if not os.access(file, os.X_OK):
                    self.log_warning(_("Script `%s` is not executable") % entry)

                self.scripts[folder].append(file)

            script_names = map(os.path.basename, self.scripts[folder])
            self.log_info(_("Activated %s scripts: %s")
                          % (folder, ", ".join(script_names) or None))


    def call_cmd(self, command, *args, **kwargs):
        call = [command] + args
        self.log_debug("EXECUTE " + " ".join(call))

        call = map(encode, call)
        p = subprocess.Popen(call, bufsize=-1)  #@NOTE: output goes to pyload

        return p


    @Expose
    def call_script(self, folder, *args, **kwargs):
        scripts = self.scripts.get(folder)

        if folder not in scripts:
            self.log_debug("Folder `%s` not found" % folder)
            return

        scripts = self.scripts.get(folder)

        if not scripts:
            self.log_debug("No script found under folder `%s`" % folder)
            return

        self.log_info(_("Executing %s scripts...") % folder)

        for file in scripts:
            try:
                p = self.call_cmd(file, args)

            except Exception, e:
                self.log_error(_("Runtime error: %s") % file,
                               e or _("Unknown error"))

            else:
                if kwargs.get('lock') or not self.config.get('unlock'):
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
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fsjoin(self.pyload.config.get("general", "download_folder"), pyfile.package().folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        file = os.path.join(dl_folder, pyfile.name)
        args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
        self.call_script("download_failed", *args)


    def download_finished(self, pyfile):
        file = pyfile.plugin.last_download
        args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
        self.call_script("download_finished", *args)


    def archive_extract_failed(self, pyfile, archive):
        args = [pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
        self.call_script("archive_extract_failed", *args)


    def archive_extracted(self, pyfile, archive):
        args = [pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
        self.call_script("archive_extracted", *args)


    def package_finished(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fsjoin(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_finished", *args)


    def package_deleted(self, pid):
        pdata = self.pyload.api.getPackageInfo(pid)

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fsjoin(self.pyload.config.get("general", "download_folder"), pdata.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        args = [pdata.pid, pdata.name, dl_folder, pdata.password]
        self.call_script("package_deleted", *args)


    def package_extract_failed(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fsjoin(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

        args = [pypack.id, pypack.name, dl_folder, pypack.password]
        self.call_script("package_extract_failed", *args)


    def package_extracted(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = fsjoin(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            dl_folder = self.pyload.config.get("general", "download_folder")

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
