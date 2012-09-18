# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""

import subprocess
from os import access, X_OK, makedirs
from os.path import basename

from module.plugins.Addon import Addon
from module.utils.fs import save_join, exists, join, listdir

class ExternalScripts(Addon):
    __name__ = "ExternalScripts"
    __version__ = "0.21"
    __description__ = """Run external scripts"""
    __config__ = [("activated", "bool", "Activated", "True")]
    __author_name__ = ("mkaay", "RaNaN", "spoob")
    __author_mail__ = ("mkaay@mkaay.de", "ranan@pyload.org", "spoob@pyload.org")

    event_list = ["unrarFinished", "allDownloadsFinished", "allDownloadsProcessed"]

    def setup(self):
        self.scripts = {}

        folders = ['download_preparing', 'download_finished', 'package_finished',
                   'before_reconnect', 'after_reconnect', 'unrar_finished',
                   'all_dls_finished', 'all_dls_processed']

        for folder in folders:

            self.scripts[folder] = []

            self.initPluginType(folder, join(pypath, 'scripts', folder))
            self.initPluginType(folder, join('scripts', folder))

        for script_type, names in self.scripts.iteritems():
            if names:
                self.logInfo((_("Installed scripts for %s: ") % script_type ) + ", ".join([basename(x) for x in names]))


    def initPluginType(self, folder, path):
        if not exists(path):
            try:
                makedirs(path)
            except :
                self.logDebug("Script folder %s not created" % folder)
                return

        for f in listdir(path):
            if f.startswith("#") or f.startswith(".") or f.startswith("_") or f.endswith("~") or f.endswith(".swp"):
                continue

            if not access(join(path,f), X_OK):
                self.logWarning(_("Script not executable:") + " %s/%s" % (folder, f))

            self.scripts[folder].append(join(path, f))

    def callScript(self, script, *args):
        try:
            cmd = [script] + [str(x) if not isinstance(x, basestring) else x for x in args]
            #output goes to pyload
            subprocess.Popen(cmd, bufsize=-1)
        except Exception, e:
            self.logError(_("Error in %(script)s: %(error)s") % { "script" :basename(script), "error": str(e)})

    def downloadPreparing(self, pyfile):
        for script in self.scripts['download_preparing']:
            self.callScript(script, pyfile.pluginname, pyfile.url, pyfile.id)

    def downloadFinished(self, pyfile):
        for script in self.scripts['download_finished']:
            self.callScript(script, pyfile.pluginname, pyfile.url, pyfile.name, pyfile.id,
                            save_join(self.core.config['general']['download_folder'], pyfile.package().folder, pyfile.name),
                            pyfile.id)


    def packageFinished(self, pypack):
        for script in self.scripts['package_finished']:
            folder = self.core.config['general']['download_folder']
            folder = save_join(folder, pypack.folder)

            self.callScript(script, pypack.name, folder, pypack.id)

    def beforeReconnecting(self, ip):
        for script in self.scripts['before_reconnect']:
            self.callScript(script, ip)

    def afterReconnecting(self, ip):
        for script in self.scripts['after_reconnect']:
            self.callScript(script, ip)

    def unrarFinished(self, folder, fname):
        for script in self.scripts["unrar_finished"]:
            self.callScript(script, folder, fname)

    def allDownloadsFinished(self):
        for script in self.scripts["all_dls_finished"]:
            self.callScript(script)

    def allDownloadsProcessed(self):
        for script in self.scripts["all_dls_processed"]:
            self.callScript(script)

