# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Plugin import Fail, encode
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns, set_cookie, set_cookies


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.53"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"       , "bool", "Activated"                                 , True),
                   ("use_premium"     , "bool", "Use premium account if available"          , True),
                   ("fallback_premium", "bool", "Fallback to free download if premium fails", True),
                   ("chk_filesize"    , "bool", "Check file size"                           , True),
                   ("revertfailed"    , "bool", "Revert to standard download if fails"      , True)]

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_NAME = None

    LEECH_HOSTER  = False
    LOGIN_ACCOUNT = True


    def init(self):
        self.PLUGIN_NAME = self.pyload.pluginManager.hosterPlugins[self.classname]['name']


    def _log(self, level, plugintype, pluginname, messages):
        return super(MultiHoster, self)._log(level,
                                             plugintype,
                                             pluginname,
                                             (self.PLUGIN_NAME,) + messages)


    def setup(self):
        self.chunk_limit     = 1
        self.multiDL         = bool(self.account)
        self.resume_download = self.premium


    def prepare(self):
        #@TODO: Recheck in 0.4.10
        plugin = self.pyload.pluginManager.hosterPlugins[self.classname]
        name   = plugin['name']
        module = plugin['module']
        klass  = getattr(module, name)

        self.get_info = klass.get_info

        if self.DIRECT_LINK is None:
            direct_dl = self.__pattern__ != r'^unmatchable$' and re.match(self.__pattern__, self.pyfile.url)
        else:
            direct_dl = self.DIRECT_LINK

        super(MultiHoster, self).prepare()

        self.direct_dl = direct_dl


    def process(self, pyfile):
        try:
            self.prepare()
            self.check_info()  #@TODO: Remove in 0.4.10

            if self.direct_dl:
                self.log_info(_("Looking for direct download link..."))
                self.handle_direct(pyfile)

                if self.link or was_downloaded():
                    self.log_info(_("Direct download link detected"))
                else:
                    self.log_info(_("Direct download link not found"))

            if not self.link and not self.last_download:
                self.preload()

                self.check_errors()
                self.check_status(getinfo=False)

                if self.premium and (not self.CHECK_TRAFFIC or self.check_traffic()):
                    self.log_info(_("Processing as premium download..."))
                    self.handle_premium(pyfile)

                elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.check_traffic()):
                    self.log_info(_("Processing as free download..."))
                    self.handle_free(pyfile)

            if not self.last_download:
                self.log_info(_("Downloading file..."))
                self.download(self.link, disposition=self.DISPOSITION)

            self.check_download()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            if self.premium:
                self.log_warning(_("Premium download failed"))
                self.restart(premium=False)

            elif self.get_config("revertfailed", True) and \
                 self.pyload.pluginManager.hosterPlugins[self.classname].get('new_module'):
                hdict = self.pyload.pluginManager.hosterPlugins[self.classname]

                tmp_module = hdict['new_module']
                tmp_name   = hdict['new_name']
                hdict.pop('new_module', None)
                hdict.pop('new_name', None)

                pyfile.initPlugin()

                hdict['new_module'] = tmp_module
                hdict['new_name']   = tmp_name

                self.restart(_("Revert to original hoster plugin"))

            else:
                raise Fail(encode(e))  #@TODO: Remove `encode` in 0.4.10


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)


    def handle_free(self, pyfile):
        if self.premium:
            raise NotImplementedError
        else:
            self.fail(_("Required premium account not found"))
