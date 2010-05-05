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
import os

class LinuxFileEvents(Hook):
    __name__ = "LinuxFileEvents"
    __version__ = "0.1"
    __description__ = """monitors files and directories for changes"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def __init__(self, core):
        Hook.__init__(self, core)
        props = {}
        self.props = props

        return #@TODO remove when working correctly
    
        if not os.name == "posix":
            return
        
        self.core.check_file(self.core.make_path("container"), _("folder for container"), True)
        self.core.check_install("pyinotify", _("pyinotify for LinuxFileEvents"))
        
        try:
            import pyinotify
        except:
            return
        wm = pyinotify.WatchManager()
        
        class FileChangeHandler(pyinotify.ProcessEvent):
            def __init__(self, hook):
                self.hook = hook
            
            def process_default(self, event):
                self.hook.fileChangeEvent(event.path)
        
        notifier = pyinotify.ThreadedNotifier(wm, FileChangeHandler(self))
        notifier.start()
        mask = pyinotify.IN_MODIFY | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
        wm.add_watch(os.path.join(self.core.path, "links.txt"), mask)
        wm.add_watch(os.path.join(self.core.path, "container"), mask, rec=True, auto_add=True)
    
    def fileChangeEvent(self, path):
        path = os.path.abspath(path)
        if self.isValidContainer(path):
            self.addNewFile(path)
    
    def isValidContainer(self, path):
        ext = [".txt", ".dlc", ".ccf", ".rsdf"]
        for e in ext:
            if path.endswith(e):
                return True
        return False
    
    def addNewFile(self, path):
        self.core.server_methods.add_package("Container", [path])
        
