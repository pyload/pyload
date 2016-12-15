# -*- coding: utf-8 -*-
#@author: and9000

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from past.utils import old_div
import os
import re
import traceback

from os.path import join
from pyload.utils import save_join, fs_encode
from pyload.plugins.hook import Hook

BUFFER_SIZE = 4096


class MergeFiles(Hook):
    __name__ = "MergeFiles"
    __version__ = "0.12"
    __description__ = """Merges parts splitted with hjsplit"""
    __config__ = [("activated", "bool", "Activated", False)]
    __threaded__ = ["packageFinished"]
    __author_name__ = "and9000"
    __author_mail__ = "me@has-no-mail.com"

    def setup(self):
        # nothing to do
        pass

    def packageFinished(self, pack):
        files = {}
        fid_dict = {}
        for fid, data in pack.getChildren().items():
            if re.search("\.[0-9]{3}$", data["name"]):
                if data["name"][:-4] not in files:
                    files[data["name"][:-4]] = []
                files[data["name"][:-4]].append(data["name"])
                files[data["name"][:-4]].sort()
                fid_dict[data["name"]] = fid

        download_folder = self.config['general']['download_folder']

        if self.config['general']['folder_per_package']:
            download_folder = save_join(download_folder, pack.folder)

        for name, file_list in files.items():
            self.logInfo("Starting merging of %s" % name)
            final_file = open(join(download_folder, fs_encode(name)), "wb")

            for splitted_file in file_list:
                self.logDebug("Merging part %s" % splitted_file)
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
                            pyfile.setProgress(old_div((size_written * 100), s_file_size))
                        else:
                            break
                    s_file.close()
                    self.logDebug("Finished merging part %s" % splitted_file)
                except Exception as e:
                    print(traceback.print_exc())
                finally:
                    pyfile.setProgress(100)
                    pyfile.setStatus("finished")
                    pyfile.release()

            final_file.close()
            self.logInfo("Finished merging of %s" % name)
