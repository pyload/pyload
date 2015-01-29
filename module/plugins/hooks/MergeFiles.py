# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import re

from traceback import print_exc

from module.plugins.Hook import Hook, threaded
from module.utils import save_join


class MergeFiles(Hook):
    __name__    = "MergeFiles"
    __type__    = "hook"
    __version__ = "0.14"

    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Merges parts splitted with hjsplit"""
    __license__     = "GPLv3"
    __authors__     = [("and9000", "me@has-no-mail.com")]


    BUFFER_SIZE = 4096


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        # nothing to do
        pass


    @threaded
    def packageFinished(self, pack):
        files = {}
        fid_dict = {}
        for fid, data in pack.getChildren().iteritems():
            if re.search("\.\d{3}$", data['name']):
                if data['name'][:-4] not in files:
                    files[data['name'][:-4]] = []
                files[data['name'][:-4]].append(data['name'])
                files[data['name'][:-4]].sort()
                fid_dict[data['name']] = fid

        download_folder = self.config['general']['download_folder']

        if self.config['general']['folder_per_package']:
            download_folder = save_join(download_folder, pack.folder)

        for name, file_list in files.iteritems():
            self.logInfo(_("Starting merging of"), name)

            with open(save_join(download_folder, name), "wb") as final_file:
                for splitted_file in file_list:
                    self.logDebug("Merging part", splitted_file)

                    pyfile = self.core.files.getFile(fid_dict[splitted_file])

                    pyfile.setStatus("processing")

                    try:
                        with open(save_join(download_folder, splitted_file), "rb") as s_file:
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
                        self.logDebug("Finished merging part", splitted_file)

                    except Exception, e:
                        print_exc()

                    finally:
                        pyfile.setProgress(100)
                        pyfile.setStatus("finished")
                        pyfile.release()

            self.logInfo(_("Finished merging of"), name)
