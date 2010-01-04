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

from module.plugins.hooks.Hook import Hook

from os.path import join, abspath

class ContainerDownload(Hook):
    def __init__(self, core):
        Hook.__init__(self, core)
        props = {}
        props['name'] = "ContainerDownload"
        props['version'] = "0.1"
        props['description'] = """add the downloaded container to current package"""
        props['author_name'] = ("mkaay")
        props['author_mail'] = ("mkaay@mkaay.de")
        self.props = props
    
    def downloadFinished(self, pyfile):
        filename = pyfile.status.filename
        if filename.endswith(".dlc") or filename.endswith(".ccf") or filename.endswith(".rsdf"):
            self.logger.info("ContainerDownload hook: adding container file")
            location = abspath(join(pyfile.folder, filename))
            newFile = self.core.file_list.collector.addLink(location)
            self.core.file_list.packager.addFileToPackage(pyfile.package.data["id"], self.core.file_list.collector.popFile(newFile))
