# -*- coding: utf-8 -*-

import os
import subprocess

from module.plugins.Hook import Hook
from module.utils import fs_encode, save_join


class ExternalScripts(Hook):
    __name__    = "ExternalScripts"
    __type__    = "hook"
    __version__ = "0.39"

    __config__ = [("activated", "bool", "Activated"         , True ),
                  ("waitend"  , "bool", "Wait script ending", False)]

    __description__ = """Run external scripts"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "ranan@pyload.org" ),
                       ("spoob"         , "spoob@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["archive_extract_failed", "archive_extracted"     ,
                  "package_extract_failed", "package_extracted"     ,
                  "all_archives_extracted", "all_archives_processed",
                  "allDownloadsFinished"  , "allDownloadsProcessed" ,
                  "packageDeleted"]
    interval   = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info    = {'oldip': None}
        self.scripts = {}

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
                self.initPluginType(folder, os.path.join(dir, 'scripts', folder))

        for script_type, names in self.scripts.iteritems():
            if names:
                self.logInfo(_("Installed scripts for: ") + script_type, ", ".join(map(os.path.basename, names)))

        self.pyload_start()


    def initPluginType(self, name, dir):
        if not os.path.isdir(dir):
            try:
                os.makedirs(dir)

            except OSError, e:
                self.logDebug(e)
                return

        for filename in os.listdir(dir):
            file = save_join(dir, filename)

            if not os.path.isfile(file):
                continue

            if filename[0] in ("#", "_") or filename.endswith("~") or filename.endswith(".swp"):
                continue

            if not os.access(file, os.X_OK):
                self.logWarning(_("Script not executable:") + " %s/%s" % (name, filename))

            self.scripts[name].append(file)


    def callScript(self, script, *args):
        try:
            cmd_args = [fs_encode(str(x) if not isinstance(x, basestring) else x) for x in args]
            cmd      = [script] + cmd_args

            self.logDebug("Executing: %s" % os.path.abspath(script), "Args: " + ' '.join(cmd_args))

            p = subprocess.Popen(cmd, bufsize=-1)  #@NOTE: output goes to pyload
            if self.getConfig('waitend'):
                p.communicate()

        except Exception, e:
            try:
                self.logError(_("Runtime error: %s") % os.path.abspath(script), e)
            except Exception:
                self.logError(_("Runtime error: %s") % os.path.abspath(script), _("Unknown error"))


    def pyload_start(self):
        for script in self.scripts['pyload_start']:
            self.callScript(script)


    def coreExiting(self):
        for script in self.scripts['pyload_restart' if self.core.do_restart else 'pyload_stop']:
            self.callScript(script)


    def beforeReconnecting(self, ip):
        for script in self.scripts['before_reconnect']:
            self.callScript(script, ip)
        self.info['oldip'] = ip


    def afterReconnecting(self, ip):
        for script in self.scripts['after_reconnect']:
            self.callScript(script, ip, self.info['oldip'])  #@TODO: Use built-in oldip in 0.4.10


    def downloadPreparing(self, pyfile):
        for script in self.scripts['download_preparing']:
            self.callScript(script, pyfile.id, pyfile.name, None, pyfile.pluginname, pyfile.url)


    def downloadFailed(self, pyfile):
        if self.config['general']['folder_per_package']:
            download_folder = save_join(self.config['general']['download_folder'], pyfile.package().folder)
        else:
            download_folder = self.config['general']['download_folder']

        for script in self.scripts['download_failed']:
            file = save_join(download_folder, pyfile.name)
            self.callScript(script, pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url)


    def downloadFinished(self, pyfile):
        if self.config['general']['folder_per_package']:
            download_folder = save_join(self.config['general']['download_folder'], pyfile.package().folder)
        else:
            download_folder = self.config['general']['download_folder']

        for script in self.scripts['download_finished']:
            file = save_join(download_folder, pyfile.name)
            self.callScript(script, pyfile.id, pyfile.name, file, pyfile.pluginname, pyfile.url)


    def archive_extract_failed(self, pyfile, archive):
        for script in self.scripts['archive_extract_failed']:
            self.callScript(script, pyfile.id, pyfile.name, archive.filename, archive.out, archive.files)


    def archive_extracted(self, pyfile, archive):
        for script in self.scripts['archive_extracted']:
            self.callScript(script, pyfile.id, pyfile.name, archive.filename, archive.out, archive.files)


    def packageFinished(self, pypack):
        if self.config['general']['folder_per_package']:
            download_folder = save_join(self.config['general']['download_folder'], pypack.folder)
        else:
            download_folder = self.config['general']['download_folder']

        for script in self.scripts['package_finished']:
            self.callScript(script, pypack.id, pypack.name, download_folder, pypack.password)


    def packageDeleted(self, pid):
        pack = self.core.api.getPackageInfo(pid)

        if self.config['general']['folder_per_package']:
            download_folder = save_join(self.config['general']['download_folder'], pack.folder)
        else:
            download_folder = self.config['general']['download_folder']

        for script in self.scripts['package_deleted']:
            self.callScript(script, pack.id, pack.name, download_folder, pack.password)


    def package_extract_failed(self, pypack):
        if self.config['general']['folder_per_package']:
            download_folder = save_join(self.config['general']['download_folder'], pypack.folder)
        else:
            download_folder = self.config['general']['download_folder']

        for script in self.scripts['package_extract_failed']:
            self.callScript(script, pypack.id, pypack.name, download_folder, pypack.password)


    def package_extracted(self, pypack):
        if self.config['general']['folder_per_package']:
            download_folder = save_join(self.config['general']['download_folder'], pypack.folder)
        else:
            download_folder = self.config['general']['download_folder']

        for script in self.scripts['package_extracted']:
            self.callScript(script, pypack.id, pypack.name, download_folder)


    def allDownloadsFinished(self):
        for script in self.scripts['all_downloads_finished']:
            self.callScript(script)


    def allDownloadsProcessed(self):
        for script in self.scripts['all_downloads_processed']:
            self.callScript(script)


    def all_archives_extracted(self):
        for script in self.scripts['all_archives_extracted']:
            self.callScript(script)


    def all_archives_processed(self):
        for script in self.scripts['all_archives_processed']:
            self.callScript(script)
