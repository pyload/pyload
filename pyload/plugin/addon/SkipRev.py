# -*- coding: utf-8 -*-

from urllib import unquote
from urlparse import urlparse

from pyload.plugin.Addon import Addon
from pyload.plugin.Plugin import SkipDownload


class SkipRev(Adoon):
    __name    = "SkipRev"
    __type    = "addon"
    __version = "0.15"

    __config = [("tokeep", "int", "Number of rev files to keep for package (-1 to auto)", -1)]

    __description = """Skip files ending with extension rev"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def _setup(self):
        super(self.pyfile.plugin, self).setup()
        if self.pyfile.hasStatus("skipped"):
            raise SkipDownload(self.pyfile.getStatusName() or self.pyfile.pluginname)


    def pyname(self, pyfile):
        url    = pyfile.url
        plugin = pyfile.plugin

        if hasattr(plugin, "info") and 'name' in plugin.info and plugin.info['name']:
            name = plugin.info['name']

        elif hasattr(plugin, "parseInfos"):
            name = next(plugin.parseInfos([url]))['name']

        elif hasattr(plugin, "getInfo"):  #@NOTE: if parseInfos was not found, getInfo should be missing too
            name = plugin.getInfo(url)['name']

        else:
            self.logWarning("Unable to grab file name")
            name = urlparse(unquote(url)).path.split('/')[-1])

        return name


    def downloadPreparing(self, pyfile):
        if pyfile.getStatusName() is "unskipped" or not pyname(pyfile).endswith(".rev"):
            return

        tokeep = self.getConfig("tokeep")

        if tokeep:
            saved = [True for link in pyfile.package().getChildren() \
                     if link.name.endswith(".rev") and (link.hasStatus("finished") or link.hasStatus("downloading"))].count(True)

            if not saved or saved < tokeep:  #: keep one rev at least in auto mode
                return

        pyfile.setCustomStatus("SkipRev", "skipped")
        pyfile.plugin.setup = _setup  #: work-around: inject status checker inside the preprocessing routine of the plugin


    def downloadFailed(self, pyfile):
        tokeep = self.getConfig("tokeep")

        if not tokeep:
            return

        for link in pyfile.package().getChildren():
            if link.hasStatus("skipped") and link.name.endswith(".rev"):
                if tokeep > -1 or pyfile.name.endswith(".rev"):
                    link.setStatus("queued")
                else:
                    link.setCustomStatus("unskipped", "queued")
                return
