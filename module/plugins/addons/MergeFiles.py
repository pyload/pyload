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
    
    @author: and9000
"""

import os
import re
import sys
import traceback

from os.path import join
from module.utils import save_join, fs_encode
from module.plugins.Addon import Addon

BUFFER_SIZE = 4096

class MergeFiles(Addon):
    __name__ = "MergeFiles"
    __version__ = "0.1"
    __description__ = "Merges parts splitted with hjsplit"
    __config__ = [
        ("activated" , "bool" , "Activated"  , "False"),
        ]
    __threaded__ = ["packageFinished"]
    __author_name__ = ("and9000")
    __author_mail__ = ("me@has-no-mail.com")

    def setup(self):
        # nothing to do
        pass
        
    def packageFinished(self, pack):
        files = {}
        fid_dict = {}
        for fid, data in pack.getChildren().iteritems():
            if re.search("\.[0-9]{3}$", data["name"]):
                if data["name"][:-4] not in files:
                    files[data["name"][:-4]] = []
                files[data["name"][:-4]].append(data["name"])
                files[data["name"][:-4]].sort()
                fid_dict[data["name"]] = fid
                
        download_folder = self.core.config['general']['download_folder']
                
        if self.core.config['general']['folder_per_package']:
            download_folder = save_join(download_folder, pack.folder)

        for name, file_list in files.iteritems():
            self.core.log.info("Starting merging of %s" % name)
            final_file = open(join(download_folder, fs_encode(name)), "wb")

            for splitted_file in file_list:
                self.core.log.debug("Merging part %s" % splitted_file)
                pyfile = self.core.files.getFile(fid_dict[splitted_file])
                pyfile.setStatus("processing")
                try:
                    s_file = open(os.path.join(download_folder, splitted_file), "rb")
                    size_written = 0
                    s_file_size = int(os.path.getsize(os.path.join(download_folder, splitted_file)))
                    while True:
                        f_buffer = s_file.read(BUFFER_SIZE)
                        if f_buffer:
                            final_file.write(f_buffer)
                            size_written += BUFFER_SIZE
                            pyfile.setProgress((size_written*100)/s_file_size)
                        else:
                            break
                    s_file.close()
                    self.core.log.debug("Finished merging part %s" % splitted_file)
                except Exception, e:
                    print traceback.print_exc()
                finally:
                    pyfile.setProgress(100)
                    pyfile.setStatus("finished")
                    pyfile.release()
                    
            final_file.close()
            self.core.log.info("Finished merging of %s" % name)
                

