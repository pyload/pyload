# -*- coding: utf-8 -*-

import os
import subprocess

from module.plugins.internal.Addon import Addon, Expose
from module.utils import fs_encode, save_join as fs_join


class ExternalScripts(Addon):
    __name__    = "ExternalScripts"
    __type__    = "hook"
    __version__ = "0.46"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated"         , True ),
                  ("lock"     , "bool", "Wait script ending", False)]

    __description__ = """Run external scripts"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "ranan@pyload.org" ),
                       ("spoob"         , "spoob@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        self.info['oldip'] = None
        self.scripts = {}

        self.event_list = ["archive_extract_failed", "archive_extracted"     ,
                           "package_extract_failed", "package_extracted"     ,
                           "all_archives_extracted", "all_archives_processed"]
        self.event_map  = {'allDownloadsFinished' : "all_downloads_finished" ,
                           'allDownloadsProcessed': "all_downloads_processed",
                           'packageDeleted'       : "package_deleted"        }

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

        for file in os.listdir(path):
            if not os.path.isfile(file):
                continue

            if file[0] in ("#", "_") or file.endswith("~") or file.endswith(".swp"):
                continue

            if not os.access(file, os.X_OK):
                self.log_warning(_("Script not executable: [%s] %s") % (name, file))

            self.scripts[name].append(file)


    @Expose
    def call(self, script, args=[], lock=False):
        try:
            script = os.path.abspath(script)
            args   = [script] + map(encode, args)

            self.log_info(_("EXECUTE [%s] %s") % (os.path.dirname(script), args))
            p = subprocess.Popen(args, bufsize=-1)  #@NOTE: output goes to pyload
            if lock:
                p.communicate()

        except Exception, e:
            self.log_error(_("Runtime error: %s") % script, e or _("Unknown error"))


    def pyload_start(self):
        lock = self.get_config('lock')
        for script in self.scripts['pyload_start']:
            self.call(script, lock=lock)


    def exit(self):
        lock = self.get_config('lock')
        for script in self.scripts['pyload_restart' if self.pyload.do_restart else 'pyload_stop']:
            self.call(script, lock=True)


    def before_reconnect(self, ip):
        lock = self.get_config('lock')
        for script in self.scripts['before_reconnect']:
            args = [ip]
            self.call(script, args, lock)
        self.info['oldip'] = ip


    def after_reconnect(self, ip):
        lock = self.get_config('lock')
        for script in self.scripts['after_reconnect']:
            args = [ip, self.info['oldip']]  #@TODO: Use built-in oldip in 0.4.10
            self.call(script, args, lock)


    def download_preparing(self, pyfile):
        lock = self.get_config('lock')
        for script in self.scripts['download_preparing']:
            args = [pyfile.id, pyfile.name, None, pyfile.pluginname, pyfile.url]
            self.call(script, args, lock)


    def download_failed(self, pyfile):
        lock = self.get_config('lock')

        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pyfile.package().folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['download_failed']:
            file = fs_join(download_folder, pyfile.name)
            args = [script, pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
            self.call(script, args, lock)


    def download_finished(self, pyfile):
        lock = self.get_config('lock')

        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pyfile.package().folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['download_finished']:
            file = fs_join(download_folder, pyfile.name)
            args = [pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url]
            self.call(script, args, lock)


    def archive_extract_failed(self, pyfile, archive):
        lock = self.get_config('lock')
        for script in self.scripts['archive_extract_failed']:
            args = [pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
            self.call(script, args, lock)


    def archive_extracted(self, pyfile, archive):
        lock = self.get_config('lock')
        for script in self.scripts['archive_extracted']:
            args = [script, pyfile.id, pyfile.name, archive.filename, archive.out, archive.files]
            self.call(script, args, lock)


    def package_finished(self, pypack):
        lock = self.get_config('lock')

        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_finished']:
            args = [pypack.id, pypack.name, download_folder, pypack.password]
            self.call(script, args, lock)


    def package_deleted(self, pid):
        lock = self.get_config('lock')
        pack = self.pyload.api.getPackageInfo(pid)

        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_deleted']:
            args = [pack.id, pack.name, download_folder, pack.password]
            self.call(script, args, lock)


    def package_extract_failed(self, pypack):
        lock = self.get_config('lock')

        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_extract_failed']:
            args = [pypack.id, pypack.name, download_folder, pypack.password]
            self.call(script, args, lock)


    def package_extracted(self, pypack):
        lock = self.get_config('lock')

        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_extracted']:
            args = [pypack.id, pypack.name, download_folder]
            self.call(script, args, lock)


    def all_downloads_finished(self):
        lock = self.get_config('lock')
        for script in self.scripts['all_downloads_finished']:
            self.call(script, lock=lock)


    def all_downloads_processed(self):
        lock = self.get_config('lock')
        for script in self.scripts['all_downloads_processed']:
            self.call(script, lock=lock)


    def all_archives_extracted(self):
        lock = self.get_config('lock')
        for script in self.scripts['all_archives_extracted']:
            self.call(script, lock=lock)


    def all_archives_processed(self):
        lock = self.get_config('lock')
        for script in self.scripts['all_archives_processed']:
            self.call(script, lock=lock)
