# -*- coding: utf-8 -*-


from pyload.core.utils import parse
from pyload.core.utils.old import safename

from .hoster import BaseHoster


class BaseDecrypter(BaseHoster):
    __name__ = "BaseDecrypter"
    __type__ = "decrypter"
    __version__ = "0.20"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Base decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def init_base(self):
        #: Put all packages here. It's a list of tuples like: ( name, [list of links], folder )
        self.packages = []
        self.links = []  #: List of urls, pyLoad will generate packagenames

    def setup_base(self):
        self.packages = []
        self.links = []

    def process(self, pyfile):
        self.decrypt(pyfile)

        if self.links:
            self._generate_packages()

        elif not self.packages:
            self.error(self._("No link grabbed"), "decrypt")

        self._create_packages()

    def decrypt(self, pyfile):
        """
        The "main" method of every decrypter plugin, you **have to** overwrite it.
        """
        raise NotImplementedError

    def _generate_packages(self):
        """
        Generate new packages from self.links.
        """
        name = self.info["pattern"].get("N")
        if name is None:
            links = [self.fixurl(url) for url in self.links]
            pdict = self.pyload.api.generate_packages(links)
            packages = [
                (name, links, parse.name(name)) for name, links in pdict.items()
            ]

        else:
            packages = [(name, self.links, parse.name(name))]

        self.packages.extend(packages)

    def _create_packages(self):
        """
        Create new packages from self.packages.
        """
        pack_folder = self.pyfile.package().folder
        pack_password = self.pyfile.package().password
        pack_queue = self.pyfile.package().queue

        folder_per_package = self.config.get("folder_per_package", "Default")

        if folder_per_package == "Default":
            folder_per_package = self.pyload.config.get("general", "folder_per_package")
        else:
            folder_per_package = folder_per_package == "Yes"

        for name, links, folder in self.packages:
            self.log_info(
                self._("Create package: {}").format(name),
                self._("{} links").format(len(links)),
            )

            links = [self.fixurl(url) for url in links]
            self.log_debug("LINKS for package " + name, links)

            pid = self.pyload.api.add_package(name, links, pack_queue)

            if pack_password:
                self.pyload.api.set_package_data(pid, {"password": pack_password})

            #: Workaround to do not break API add_package method
            def set_folder(x):
                return self.pyload.api.set_package_data(
                    pid, {"folder": safename(x or "")}
                )

            if not folder_per_package:
                folder = pack_folder

            elif not folder or folder == name:
                folder = parse.name(name)

            self.log_info(
                self._("Save package `{name}` to folder: {folder}").format(
                    name=name, folder=folder
                )
            )

            set_folder(folder)
