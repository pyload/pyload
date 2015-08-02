# -*- coding: utf-8 -*-

import urlparse

from module.plugins.internal.Hoster import Hoster, _fixurl
from module.utils import save_path as safe_filename


class Crypter(Hoster):
    __name__    = "Crypter"
    __type__    = "crypter"
    __version__ = "0.07"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),  #: Overrides pyload.config.get("general", "folder_per_package")
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Base decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    html = None  #: Last html loaded  #@TODO: Move to Hoster


    def __init__(self, pyfile):
        super(Crypter, self).__init__(pyfile)

        #: Put all packages here. It's a list of tuples like: ( name, [list of links], folder )
        self.packages = []

        #: List of urls, pyLoad will generate packagenames
        self.urls = []


    def process(self, pyfile):
        """
        Main method
        """
        self.decrypt(pyfile)

        if self.urls:
            self._generate_packages()

        elif not self.packages:
            self.error(_("No link grabbed"), "decrypt")

        self._create_packages()


    def decrypt(self, pyfile):
        raise NotImplementedError


    def _generate_packages(self):
        """
        Generate new packages from self.urls
        """
        packages = [(name, links, None) for name, links in self.pyload.api.generatePackages(self.urls).items()]
        self.packages.extend(packages)


    def _create_packages(self):
        """
        Create new packages from self.packages
        """
        package_folder   = self.pyfile.package().folder
        package_password = self.pyfile.package().password
        package_queue    = self.pyfile.package().queue

        folder_per_package    = self.pyload.config.get("general", "folder_per_package")
        use_subfolder         = self.get_config('use_subfolder', folder_per_package)
        subfolder_per_package = self.get_config('subfolder_per_package', True)

        for name, links, folder in self.packages:
            self.log_debug("Parsed package: %s" % name,
                          "%d links" % len(links),
                          "Saved to folder: %s" % folder if folder else "Saved to download folder")

            pid = self.pyload.api.addPackage(name, map(self.fixurl, links), package_queue)

            if package_password:
                self.pyload.api.setPackageData(pid, {'password': package_password})

            #: Workaround to do not break API addPackage method
            set_folder = lambda x: self.pyload.api.setPackageData(pid, {'folder': x or ""})

            if use_subfolder:
                if not subfolder_per_package:
                    set_folder(package_folder)
                    self.log_debug("Set package %(name)s folder to: %(folder)s" % {'name': name, 'folder': folder})

                elif not folder_per_package or name is not folder:
                    if not folder:
                        folder = urlparse.urlparse(_fixurl(name)).path.split("/")[-1]

                    set_folder(safe_filename(folder))
                    self.log_debug("Set package %(name)s folder to: %(folder)s" % {'name': name, 'folder': folder})

            elif folder_per_package:
                set_folder(None)
