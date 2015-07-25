# -*- coding: utf-8 -*-

import os
import subprocess

from module.plugins.internal.Addon import Addon
from module.utils import fs_encode, save_join as fs_join


class ExternalScripts(Addon):
    __name__    = "ExternalScripts"
    __type__    = "hook"
    __version__ = "0.43"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated"         , True ),
                  ("waitend"  , "bool", "Wait script ending", False)]

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
            self.scripts[folder] = []
            for dir in (pypath, ''):
                self.init_plugin_type(folder, os.path.join(dir, 'scripts', folder))

        for script_type, names in self.scripts.items():
            if names:
                self.log_info(_("Installed scripts for: ") + script_type, ", ".join(map(os.path.basename, names)))

        self.pyload_start()


    def init_plugin_type(self, name, dir):
        if not os.path.isdir(dir):
            try:
                os.makedirs(dir)

            except OSError, e:
                self.log_debug(e)
                return

        for filename in os.listdir(dir):
            file = fs_join(dir, filename)

            if not os.path.isfile(file):
                continue

            if filename[0] in ("#", "_") or filename.endswith("~") or filename.endswith(".swp"):
                continue

            if not os.access(file, os.X_OK):
                self.log_warning(_("Script not executable:") + " %s/%s" % (name, filename))

            self.scripts[name].append(file)


    def call_script(self, script, *args):
        try:
            cmd_args = (fs_encode(x) if isinstande(x, basestring) else str(x) for x in args)  #@NOTE: `fs_encode` -> `encode` in 0.4.10

            self.log_debug("Executing: %s" % os.path.abspath(script), "Args: " + ' '.join(cmd_args))

            cmd = (script,) + cmd_args

            p = subprocess.Popen(cmd, bufsize=-1)  #@NOTE: output goes to pyload
            if self.get_config('waitend'):
                p.communicate()

        except Exception, e:
            try:
                self.log_error(_("Runtime error: %s") % os.path.abspath(script), e)
            except Exception:
                self.log_error(_("Runtime error: %s") % os.path.abspath(script), _("Unknown error"))


    def pyload_start(self):
        for script in self.scripts['pyload_start']:
            self.call_script(script)


    def exit(self):
        for script in self.scripts['pyload_restart' if self.pyload.do_restart else 'pyload_stop']:
            self.call_script(script)


    def before_reconnect(self, ip):
        for script in self.scripts['before_reconnect']:
            self.call_script(script, ip)
        self.info['oldip'] = ip


    def after_reconnect(self, ip):
        for script in self.scripts['after_reconnect']:
            self.call_script(script, ip, self.info['oldip'])  #@TODO: Use built-in oldip in 0.4.10


    def download_preparing(self, pyfile):
        for script in self.scripts['download_preparing']:
            self.call_script(script, pyfile.id, pyfile.name, None, pyfile.pluginname, pyfile.url)


    def download_failed(self, pyfile):
        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pyfile.package().folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['download_failed']:
            file = fs_join(download_folder, pyfile.name)
            self.call_script(script, pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url)


    def download_finished(self, pyfile):
        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pyfile.package().folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['download_finished']:
            file = fs_join(download_folder, pyfile.name)
            self.call_script(script, pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url)


    def archive_extract_failed(self, pyfile, archive):
        for script in self.scripts['archive_extract_failed']:
            self.call_script(script, pyfile.id, pyfile.name, archive.filename, archive.out, archive.files)


    def archive_extracted(self, pyfile, archive):
        for script in self.scripts['archive_extracted']:
            self.call_script(script, pyfile.id, pyfile.name, archive.filename, archive.out, archive.files)


    def package_finished(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_finished']:
            self.call_script(script, pypack.id, pypack.name, download_folder, pypack.password)


    def package_deleted(self, pid):
        pack = self.pyload.api.getPackageInfo(pid)

        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_deleted']:
            self.call_script(script, pack.id, pack.name, download_folder, pack.password)


    def package_extract_failed(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_extract_failed']:
            self.call_script(script, pypack.id, pypack.name, download_folder, pypack.password)


    def package_extracted(self, pypack):
        if self.pyload.config.get("general", "folder_per_package"):
            download_folder = fs_join(self.pyload.config.get("general", "download_folder"), pypack.folder)
        else:
            download_folder = self.pyload.config.get("general", "download_folder")

        for script in self.scripts['package_extracted']:
            self.call_script(script, pypack.id, pypack.name, download_folder)


    def all_downloads_finished(self):
        for script in self.scripts['all_downloads_finished']:
            self.call_script(script)


    def all_downloads_processed(self):
        for script in self.scripts['all_downloads_processed']:
            self.call_script(script)


    def all_archives_extracted(self):
        for script in self.scripts['all_archives_extracted']:
            self.call_script(script)


    def all_archives_processed(self):
        for script in self.scripts['all_archives_processed']:
            self.call_script(script)
