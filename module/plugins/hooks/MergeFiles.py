# -*- coding: utf-8 -*-

import os
import re
import traceback

from module.plugins.Hook import Hook, threaded
from module.utils import safe_join, fs_encode


class MergeFiles(Hook):
    __name__ = "MergeFiles"
    __type__ = "hook"
    __version__ = "0.12"

    __config__ = [("activated", "bool", "Activated", False)]

    __description__ = """Merges parts splitted with hjsplit"""
    __author_name__ = "and9000"
    __author_mail__ = "me@has-no-mail.com"

    BUFFER_SIZE = 4096


    def setup(self):
        # nothing to do
        pass

    @threaded
    def packageFinished(self, pack):
        files = {}
        fid_dict = {}
        for fid, data in pack.getChildren().iteritems():
            if re.search("\.[0-9]{3}$", data['name']):
                if data['name'][:-4] not in files:
                    files[data['name'][:-4]] = []
                files[data['name'][:-4]].append(data['name'])
                files[data['name'][:-4]].sort()
                fid_dict[data['name']] = fid

        download_folder = self.config['general']['download_folder']

        if self.config['general']['folder_per_package']:
            download_folder = safe_join(download_folder, pack.folder)

        for name, file_list in files.iteritems():
            self.logInfo("Starting merging of %s" % name)
            final_file = open(safe_join(download_folder, name), "wb")

            for splitted_file in file_list:
                self.logDebug("Merging part %s" % splitted_file)
                pyfile = self.core.files.getFile(fid_dict[splitted_file])
                pyfile.setStatus("processing")
                try:
                    s_file = open(os.path.join(download_folder, splitted_file), "rb")
                    size_written = 0
                    s_file_size = int(os.path.getsize(os.path.join(download_folder, splitted_file)))
                    while True:
                        f_buffer = s_file.read(self.BUFFER_SIZE)
                        if f_buffer:
                            final_file.write(f_buffer)
                            size_written += self.BUFFER_SIZE
                            pyfile.setProgress((size_written * 100) / s_file_size)
                        else:
                            break
                    s_file.close()
                    self.logDebug("Finished merging part %s" % splitted_file)
                except Exception, e:
                    print traceback.print_exc()
                finally:
                    pyfile.setProgress(100)
                    pyfile.setStatus("finished")
                    pyfile.release()

            final_file.close()
            self.logInfo("Finished merging of %s" % name)
