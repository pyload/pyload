# -*- coding: utf-8 -*-

from .Base import Base
from .misc import parse_name, safename


class Crypter(Base):
    __name__ = "Crypter"
    __type__ = "crypter"
    __version__ = "0.20"
    __status__ = "stable"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

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
            self.error(_("No link grabbed"), "decrypt")

        self._create_packages()

    def decrypt(self, pyfile):
        """
        The "main" method of every crypter plugin, you **have to** overwrite it
        """
        raise NotImplementedError

    def _generate_packages(self):
        """
        Generate new packages from self.links
        """
        name = self.info['pattern'].get("N")
        if name is None:
            links = map(self.fixurl, self.links)
            pdict = self.pyload.api.generatePackages(links)
            packages = [(_name, _links, parse_name(_name))
                        for _name, _links in pdict.items()]

        else:
            packages = [(name, self.links, parse_name(name))]

        self.packages.extend(packages)

    def _create_packages(self):
        """
        Create new packages from self.packages
        """
        pack_folder = self.pyfile.package().folder
        pack_password = self.pyfile.package().password
        pack_queue = self.pyfile.package().queue

        folder_per_package = self.config.get('folder_per_package', "Default")

        if folder_per_package == "Default":
            folder_per_package = self.pyload.config.get(
                'general', 'folder_per_package')
        else:
            folder_per_package = folder_per_package == "Yes"

        for name, links, folder in self.packages:
            self.log_info(_("Create package: %s") % name,
                          _("%d links") % len(links))

            links = map(self.fixurl, links)
            self.log_debug("LINKS for package " + name, *links)

            pid = self.pyload.api.addPackage(name, links, pack_queue)

            if pack_password:
                self.pyload.api.setPackageData(
                    pid, {'password': pack_password})

            #: Workaround to do not break API addPackage method
            set_folder = lambda x: self.pyload.api.setPackageData(
                pid, {'folder': safename(x or "")})

            if not folder_per_package:
                folder = pack_folder

            elif not folder or folder == name:
                folder = parse_name(name)

            self.log_info(_("Save package `%(name)s` to folder: %(folder)s")
                          % {'name': name, 'folder': folder})

            set_folder(folder)
