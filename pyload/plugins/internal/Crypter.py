# -*- coding: utf-8 -*-

from pyload.plugins.Plugin import Plugin
from pyload.utils import save_filename


class Crypter(Plugin):
    __name__    = "Crypter"
    __type__    = "crypter"
    __version__ = "0.05"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),  #: Overrides core.config['general']['folder_per_package']
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Base decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    html = None  #: last html loaded


    def __init__(self, pyfile):
        #: Put all packages here. It's a list of tuples like: ( name, [list of links], folder )
        self.packages = []

        #: List of urls, pyLoad will generate packagenames
        self.urls = []

        Plugin.__init__(self, pyfile)


    def process(self, pyfile):
        """ main method """

        self.decrypt(pyfile)

        if self.urls:
            self.generatePackages()

        elif not self.packages:
            self.error(_("No link extracted"), "decrypt")

        self.createPackages()


    def decrypt(self, pyfile):
        raise NotImplementedError


    def generatePackages(self):
        """ generate new packages from self.urls """

        packages = map(lambda name, links: (name, links, None), self.core.api.generatePackages(self.urls).iteritems())
        self.packages.extend(packages)


    def createPackages(self):
        """ create new packages from self.packages """

        package_folder = self.pyfile.package().folder
        package_password = self.pyfile.package().password
        package_queue = self.pyfile.package().queue

        folder_per_package = self.core.config['general']['folder_per_package']
        try:
            use_subfolder = self.getConfig('use_subfolder')
        except:
            use_subfolder = folder_per_package
        try:
            subfolder_per_package = self.getConfig('subfolder_per_package')
        except:
            subfolder_per_package = True

        for pack in self.packages:
            name, links, folder = pack

            self.logDebug("Parsed package: %s" % name,
                          "%d links" % len(links),
                          "Saved to folder: %s" % folder if folder else "Saved to download folder")

            links = map(lambda x: x.decode("utf-8"), links)

            pid = self.core.api.addPackage(name, links, package_queue)

            if package_password:
                self.core.api.setPackageData(pid, {"password": package_password})

            setFolder = lambda x: self.core.api.setPackageData(pid, {"folder": x or ""})  #: Workaround to do not break API addPackage method

            if use_subfolder:
                if not subfolder_per_package:
                    setFolder(package_folder)
                    self.logDebug("Set package %(name)s folder to: %(folder)s" % {"name": name, "folder": folder})

                elif not folder_per_package or name != folder:
                    if not folder:
                        folder = name.replace("http://", "").replace(":", "").replace("/", "_").replace("\\", "_")

                    folder = save_filename(folder)  #@TODO: move to core code

                    setFolder(folder)
                    self.logDebug("Set package %(name)s folder to: %(folder)s" % {"name": name, "folder": folder})

            elif folder_per_package:
                setFolder(None)
