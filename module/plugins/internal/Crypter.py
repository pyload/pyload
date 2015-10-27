# -*- coding: utf-8 -*-

from module.plugins.internal.Base import Base, create_getInfo, parse_fileInfo
from module.plugins.internal.utils import fixname, parse_name


class Crypter(Base):
    __name__    = "Crypter"
    __type__    = "crypter"
    __version__ = "0.14"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"            , "bool", "Activated"                          , True),
                   ("use_premium"          , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"          , True),  #: Overrides pyload.config.get("general", "folder_per_package")
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Base decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init_base(self):
        self.packages = []  #: Put all packages here. It's a list of tuples like: ( name, [list of links], folder )
        self.links     = []  #: List of urls, pyLoad will generate packagenames


    def setup_base(self):
        self.packages = []
        self.links     = []


    def process(self, pyfile):
        """
        Main method
        """
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
        packages = [(name, links, None) for name, links in self.pyload.api.generatePackages(self.links).items()]
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
            self.log_info(_("Parsed package: %s")  % name,
                          _("Found %d links")      % len(links),
                          _("Saved to folder: %s") % folder if folder else _("Saved to default download folder"))

            links = map(self.fixurl, links)
            self.log_debug("LINKS for package " + name, *links)

            pid = self.pyload.api.addPackage(name, links, package_queue)

            if package_password:
                self.pyload.api.setPackageData(pid, {'password': package_password})

            #: Workaround to do not break API addPackage method
            set_folder = lambda x="": self.pyload.api.setPackageData(pid, {'folder': fixname(x)})

            if use_subfolder:
                if not subfolder_per_package:
                    set_folder(package_folder)
                    self.log_debug("Set package %(name)s folder to: %(folder)s" % {'name': name, 'folder': folder})

                elif not folder_per_package or name is not folder:
                    if not folder:
                        folder = parse_name(name)

                    set_folder(folder)
                    self.log_debug("Set package %(name)s folder to: %(folder)s" % {'name': name, 'folder': folder})

            elif folder_per_package:
                set_folder()
