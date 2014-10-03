# -*- coding: utf-8 -*-

from pyload.plugins.Plugin import Plugin


class Crypter(Plugin):
    __name__ = "Crypter"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = None

    __description__ = """Base decrypter plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"


    def __init__(self, pyfile):
        Plugin.__init__(self, pyfile)

        #: Put all packages here. It's a list of tuples like: ( name, [list of links], folder )
        self.packages = []

        #: List of urls, pyLoad will generate packagenames
        self.urls = []

        self.multiDL = True
        self.limitDL = 0


    def process(self, pyfile):
        """ main method """
        self.decrypt(pyfile)
        self.createPackages()


    def decrypt(self, pyfile):
        raise NotImplementedError


    def createPackages(self):
        """ create new packages from self.packages """
        for pack in self.packages:

            name, links, folder = pack

            self.logDebug("Parsed package %(name)s with %(len)d links" % {"name": name, "len": len(links)})

            links = [x.decode("utf-8") for x in links]

            pid = self.api.addPackage(name, links, self.pyfile.package().queue)

            if name != folder is not None:
                self.api.setPackageData(pid, {"folder": folder})  #: Due to not break API addPackage method right now
                self.logDebug("Set package %(name)s folder to %(folder)s" % {"name": name, "folder": folder})

            if self.pyfile.package().password:
                self.api.setPackageData(pid, {"password": self.pyfile.package().password})

        if self.urls:
            self.api.generateAndAddPackages(self.urls)
