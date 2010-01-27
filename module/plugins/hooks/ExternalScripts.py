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
    
    @author: mkaay
    @interface-version: 0.1
"""

from module.plugins.Hook import Hook
import subprocess
from os import listdir, sep
from os.path import join

class ExternalScripts(Hook):
    def __init__(self, core):
        Hook.__init__(self, core)
        props = {}
        props['name'] = "ExternalScripts"
        props['version'] = "0.1"
        props['description'] = """run external scripts"""
        props['author_name'] = ("mkaay", "RaNaN", "spoob")
        props['author_mail'] = ("mkaay@mkaay.de", "ranan@pyload.org", "spoob@pyload.org")
        self.props = props
        self.core = core
        self.scripts = {}
        
        script_folders = ['scripts'+sep+'download_preparing'+sep,
                          'scripts'+sep+'download_finished'+sep,
                          'scripts'+sep+'package_finished'+sep,
                          'scripts'+sep+'before_reconnect'+sep,
                          'scripts'+sep+'after_reconnect'+sep]
        self.core.check_file(script_folders, _("folders for scripts"), True)
        
        f = lambda x: False if x.startswith("#") or x.endswith("~") else True
        self.scripts = {}

        folder = join(self.core.path, "scripts")

        self.scripts['download_preparing'] = filter(f, listdir(join(folder, 'download_preparing')))
        self.scripts['download_finished'] = filter(f, listdir(join(folder, 'download_finished')))
        self.scripts['package_finished'] = filter(f, listdir(join(folder, 'package_finished')))
        self.scripts['before_reconnect'] = filter(f, listdir(join(folder, 'before_reconnect')))
        self.scripts['after_reconnect'] = filter(f, listdir(join(folder, 'after_reconnect')))

        for script_type, script_name in self.scripts.iteritems():
            if script_name != []:
                self.logger.info("Installed %s Scripts: %s" % (script_type, ", ".join(script_name)))

        #~ self.core.logger.info("Installed Scripts: %s" % str(self.scripts))

        self.folder = folder
    
    def downloadStarts(self, pyfile):
    	for script in self.scripts['download_preparing']:
            try:
                out = subprocess.Popen([join(self.folder, 'download_preparing', script), pyfile.plugin.props['name'], pyfile.url], stdout=subprocess.PIPE)
                out.wait()
            except:
                pass
    
    def downloadFinished(self, pyfile):
        for script in self.scripts['download_finished']:
            try:
                out = subprocess.Popen([join(self.folder, 'download_finished', script), pyfile.plugin.props['name'], pyfile.url, pyfile.status.name, \
                join(self.core.path,self.core.config['general']['download_folder'], pyfile.folder, pyfile.status.name)], stdout=subprocess.PIPE)
            except:
                pass
    
    def packageFinished(self, pypack):
        """
            not implemented!
        """
        pass
    
    def beforeReconnecting(self, ip):
        for script in self.scripts['before_reconnect']:
            try:
                out = subprocess.Popen([join(self.folder, 'before_reconnect', script), ip], stdout=subprocess.PIPE)
                out.wait()
            except:
                pass
    
    def afterReconnecting(self, ip):
        for script in self.scripts['after_reconnect']:
            try:
                out = subprocess.Popen([join(self.folder, 'download_preparing', script), ip], stdout=subprocess.PIPE)
            except:
                pass
