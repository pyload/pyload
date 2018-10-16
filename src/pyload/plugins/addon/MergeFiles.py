# -*- coding: utf-8 -*-
import os
import re
from builtins import _

from pyload.plugins.internal.addon import Addon
from pyload.plugins.utils import threaded


class MergeFiles(Addon):
    __name__ = "MergeFiles"
    __type__ = "addon"
    __version__ = "0.22"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __config__ = [("activated", "bool", "Activated", False)]

    __description__ = """Merges parts splitted with hjsplit"""
    __license__ = "GPLv3"
    __authors__ = [("and9000", "me@has-no-mail.com")]

    BUFFER_SIZE = 4096

    @threaded
    def package_finished(self, pack):
        files = {}
        fid_dict = {}
        for fid, data in pack.getChildren().items():
            if re.search(r"\.\d{3}$", data["name"]):
                if data["name"][:-4] not in files:
                    files[data["name"][:-4]] = []
                files[data["name"][:-4]].append(data["name"])
                files[data["name"][:-4]].sort()
                fid_dict[data["name"]] = fid

        dl_folder = self.pyload.config.get("general", "download_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pack.folder)

        for name, file_list in files.items():
            self.log_info(_("Starting merging of"), name)

            with open(os.path.join(dl_folder, name), "wb") as final_file:
                for splitted_file in file_list:
                    self.log_debug("Merging part", splitted_file)

                    pyfile = self.pyload.files.getFile(fid_dict[splitted_file])

                    pyfile.setStatus("processing")

                    try:
                        with open(
                            os.path.join(dl_folder, splitted_file), "rb"
                        ) as s_file:
                            size_written = 0
                            s_file_size = int(
                                os.path.getsize(os.path.join(dl_folder, splitted_file))
                            )
                            while True:
                                f_buffer = s_file.read(self.BUFFER_SIZE)
                                if f_buffer:
                                    final_file.write(f_buffer)
                                    size_written += self.BUFFER_SIZE
                                    pyfile.setProgress(
                                        (size_written * 100) // s_file_size
                                    )
                                else:
                                    break
                        self.log_debug("Finished merging part", splitted_file)

                    except Exception as e:
                        self.log_error(e, trace=True)

                    finally:
                        pyfile.setProgress(100)
                        pyfile.setStatus("finished")
                        pyfile.release()

            self.log_info(_("Finished merging of"), name)
