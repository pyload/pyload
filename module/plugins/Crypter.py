# -*- coding: utf-8 -*-

from module.plugins.Plugin import Plugin


class Crypter(Plugin):
    __name__ = "Crypter"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = None

    __description__ = """Base decrypter plugin"""
    __authors__ = [("mkaay", "mkaay@mkaay.de")]


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

            self.log.debug("Parsed package %(name)s with %(len)d links" % { "name" : pack[0], "len" : len(pack[1]) } )

            links = [x.decode("utf-8") for x in pack[1]]

            pid = self.core.api.addPackage(pack[0], links, self.pyfile.package().queue)

            if self.pyfile.package().password:
                self.core.api.setPackageData(pid, {"password": self.pyfile.package().password})

        if self.urls:
            self.core.api.generateAndAddPackages(self.urls)
