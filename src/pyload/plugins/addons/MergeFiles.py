# -*- coding: utf-8 -*-
import os
import re

from ..base.addon import BaseAddon, threaded


class MergeFiles(BaseAddon):
    __name__ = "MergeFiles"
    __type__ = "addon"
    __version__ = "0.24"
    __status__ = "testing"

    __config__ = [("enabled", "bool", "Activated", False)]

    __description__ = """Merges parts splitted with hjsplit"""
    __license__ = "GPLv3"
    __authors__ = [("and9000", "me@has-no-mail.com")]

    BUFFER_SIZE = 4096

    @threaded
    def package_finished(self, pack):
        files = {}
        fid_dict = {}
        for fid, data in pack.get_children().items():
            if re.search(r"\.\d{3}$", data["name"]):
                if data["name"][:-4] not in files:
                    files[data["name"][:-4]] = []
                files[data["name"][:-4]].append(data["name"])
                files[data["name"][:-4]].sort()
                fid_dict[data["name"]] = fid

        dl_folder = self.pyload.config.get("general", "storage_folder")

        if self.pyload.config.get("general", "folder_per_package"):
            dl_folder = os.path.join(dl_folder, pack.folder)

        for name, file_list in files.items():
            self.log_info(self._("Starting merging of"), name)

            with open(os.path.join(dl_folder, name), mode="wb") as final_file:
                for splitted_file in file_list:
                    self.log_debug("Merging part", splitted_file)

                    pyfile = self.pyload.files.get_file(fid_dict[splitted_file])

                    pyfile.set_status("processing")

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
                                    pyfile.set_progress(
                                        (size_written * 100) // s_file_size
                                    )
                                else:
                                    break
                        self.log_debug("Finished merging part", splitted_file)

                    except Exception as exc:
                        self.log_error(
                            exc,
                            exc_info=self.pyload.debug > 1,
                            stack_info=self.pyload.debug > 2,
                        )

                    finally:
                        pyfile.set_progress(100)
                        pyfile.set_status("finished")
                        pyfile.release()

            self.log_info(self._("Finished merging of"), name)
