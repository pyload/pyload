# -*- coding: utf-8 -*-

import subprocess

from itertools import chain
from os import listdir, access, X_OK, makedirs
from os.path import join, exists, basename, abspath

from module.plugins.Hook import Hook
from module.utils import save_join


class ExternalScripts(Hook):
    __name__ = "ExternalScripts"
    __type__ = "hook"
    __version__ = "0.24"

    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Run external scripts"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de"),
                   ("RaNaN", "ranan@pyload.org"),
                   ("spoob", "spoob@pyload.org"),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["archive_extracted", "package_extracted", "all_archives_extracted", "all_archives_processed",
                  "allDownloadsFinished", "allDownloadsProcessed"]


    def setup(self):
        self.scripts = {}

        folders = ["download_preparing", "download_finished", "all_downloads_finished", "all_downloads_processed",
                   "before_reconnect", "after_reconnect",
                   "package_finished", "package_extracted",
                   "archive_extracted", "all_archives_extracted", "all_archives_processed",
                   # deprecated folders
                   "unrar_finished", "all_dls_finished", "all_dls_processed"]

        for folder in folders:
            self.scripts[folder] = []

            self.initPluginType(folder, join(pypath, 'scripts', folder))
            self.initPluginType(folder, join('scripts', folder))

        for script_type, names in self.scripts.iteritems():
            if names:
                self.logInfo(_("Installed scripts for"), script_type, ", ".join([basename(x) for x in names]))


    def initPluginType(self, folder, path):
        if not exists(path):
            try:
                makedirs(path)
            except:
                self.logDebug("Script folder %s not created" % folder)
                return

        for f in listdir(path):
            if f.startswith("#") or f.startswith(".") or f.startswith("_") or f.endswith("~") or f.endswith(".swp"):
                continue

            if not access(join(path, f), X_OK):
                self.logWarning(_("Script not executable:") + " %s/%s" % (folder, f))

            self.scripts[folder].append(join(path, f))


    def callScript(self, script, *args):
        try:
            cmd = [script] + [str(x) if not isinstance(x, basestring) else x for x in args]
            self.logDebug("Executing", abspath(script), " ".join(cmd))
            #output goes to pyload
            subprocess.Popen(cmd, bufsize=-1)
        except Exception, e:
            self.logError(_("Error in %(script)s: %(error)s") % {"script": basename(script), "error": e})


    def downloadPreparing(self, pyfile):
        for script in self.scripts['download_preparing']:
            self.callScript(script, pyfile.pluginname, pyfile.url, pyfile.id)


    def downloadFinished(self, pyfile):
        download_folder = self.config['general']['download_folder']
        for script in self.scripts['download_finished']:
            filename = save_join(download_folder, pyfile.package().folder, pyfile.name)
            self.callScript(script, pyfile.pluginname, pyfile.url, pyfile.name, filename, pyfile.id)


    def packageFinished(self, pypack):
        download_folder = self.config['general']['download_folder']
        for script in self.scripts['package_finished']:
            folder = save_join(download_folder, pypack.folder)
            self.callScript(script, pypack.name, folder, pypack.password, pypack.id)


    def beforeReconnecting(self, ip):
        for script in self.scripts['before_reconnect']:
            self.callScript(script, ip)


    def afterReconnecting(self, ip):
        for script in self.scripts['after_reconnect']:
            self.callScript(script, ip)


    def archive_extracted(self, pyfile, folder, filename, files):
        for script in self.scripts['archive_extracted']:
            self.callScript(script, folder, filename, files)
        for script in self.scripts['unrar_finished']:  #: deprecated
            self.callScript(script, folder, filename)


    def package_extracted(self, pypack):
        download_folder = self.config['general']['download_folder']
        for script in self.scripts['package_extracted']:
            folder = save_join(download_folder, pypack.folder)
            self.callScript(script, pypack.name, folder, pypack.password, pypack.id)


    def all_archives_extracted(self):
        for script in self.scripts['all_archives_extracted']:
            self.callScript(script)


    def all_archives_processed(self):
        for script in self.scripts['all_archives_processed']:
            self.callScript(script)


    def allDownloadsFinished(self):
        for script in chain(self.scripts['all_downloads_finished'], self.scripts['all_dls_finished']):
            self.callScript(script)


    def allDownloadsProcessed(self):
        for script in chain(self.scripts['all_downloads_processed'], self.scripts['all_dls_processed']):
            self.callScript(script)
