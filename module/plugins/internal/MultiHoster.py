# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Plugin import Fail, Retry
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns, set_cookies


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.43"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_ACCOUNT = True


    def setup(self):
        self.chunk_limit     = 1
        self.multi_dl        = bool(self.account)
        self.resume_download = self.premium


    def prepare(self):
        self.html      = ""
        self.link      = ""     #@TODO: Move to Hoster in 0.4.10
        self.direct_dl = False  #@TODO: Move to Hoster in 0.4.10

        if not self.get_config('use_premium', True):
            self.retry_free()

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if self.DIRECT_LINK is None:
            self.direct_dl = self.__pattern__ != r'^unmatchable$' and re.match(self.__pattern__, self.pyfile.url)
        else:
            self.direct_dl = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def process(self, pyfile):
        try:
            self.prepare()

            if self.direct_dl:
                self.check_info()
                self.log_debug("Looking for direct download link...")
                self.handle_direct(pyfile)

            if not self.link and not self.last_download:
                self.preload()

                self.check_errors()
                self.check_status(getinfo=False)

                if self.premium and (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                    self.log_debug("Handled as premium download")
                    self.handle_premium(pyfile)

                elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                    self.log_debug("Handled as free download")
                    self.handle_free(pyfile)

            self.download(self.link, ref=False, disposition=True)
            self.check_file()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            err = str(e)  #@TODO: Recheck in 0.4.10

            if self.premium:
                self.log_warning(_("Premium download failed"))
                self.retry_free()

            elif self.get_config("revertfailed", True) \
                 and "new_module" in self.core.pluginManager.hosterPlugins[self.__name__]:
                hdict = self.core.pluginManager.hosterPlugins[self.__name__]

                tmp_module = hdict['new_module']
                tmp_name   = hdict['new_name']
                hdict.pop('new_module', None)
                hdict.pop('new_name', None)

                pyfile.initPlugin()

                hdict['new_module'] = tmp_module
                hdict['new_name']   = tmp_name

                raise Retry(_("Revert to original hoster plugin"))

            else:
                raise Fail(err)


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)


    def handle_free(self, pyfile):
        if self.premium:
            raise NotImplementedError
        else:
            self.fail(_("Required premium account not found"))
