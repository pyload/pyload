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
from os.path import join, abspath
import subprocess
from os import remove

class Mp3Convert(Hook):
    def __init__(self, core):
        Hook.__init__(self, core)
        props = {}
        props['name'] = "Mp3Convert"
        props['version'] = "0.1"
        props['description'] = """converts files like videos to mp3"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.readConfig()
    
    def downloadFinished(self, pyfile):
        plugin = pyfile.plugin.props['name']
        if plugin == "YoutubeCom":
            filename = pyfile.status.filename[:-4]
            cmd = ['ffmpeg -i "%s" -vn -ar 44100 -ac 2 -ab 192k "%s.mp3"' % (abspath(join(pyfile.folder, pyfile.status.filename)), abspath(join(pyfile.folder, filename)))]
            converter = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            converter.wait()
            if self.config["removeRegularFile"]:
                remove(abspath(join(pyfile.folder, pyfile.status.filename)))
            self.logger.info("Mp3Convert: Converterd %s to Mp3" % filename)

    def setup(self):
        self.configParser.set(self.props["name"], {"option": "removeRegularFile", "type": "bool", "name": "Remove Regular Files"}, False)
