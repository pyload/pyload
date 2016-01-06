# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Plugin import Fail
from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import encode


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.59"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    DIRECT_LINK   = None
    LEECH_HOSTER  = False
    LOGIN_ACCOUNT = True


    def init(self):
        self.PLUGIN_NAME = self.pyload.pluginManager.hosterPlugins.get(self.classname)['name']


    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.PLUGIN_NAME,) + messages
        return super(MultiHoster, self)._log(level, plugintype, pluginname, messages)


    def setup(self):
        self.chunk_limit     = 1
        self.multiDL         = bool(self.account)
        self.resume_download = self.premium


    #@TODO: Recheck in 0.4.10
    def setup_base(self):
        klass = self.pyload.pluginManager.loadClass("hoster", self.classname)
        self.get_info = klass.get_info

        super(MultiHoster, self).setup_base()


    def _prepare(self):
        super(MultiHoster, self)._prepare()

        if self.DIRECT_LINK is None:
            self.direct_dl = self.__pattern__ != r'^unmatchable$' and re.match(self.__pattern__, self.pyfile.url)
        else:
            self.direct_dl = self.DIRECT_LINK


    def _process(self, thread):
        try:
            super(MultiHoster, self)._process(thread)

        except Fail, e:
            if self.config.get('revertfailed', True) and \
               self.pyload.pluginManager.hosterPlugins.get(self.classname).get('new_module'):
                hdict = self.pyload.pluginManager.hosterPlugins.get(self.classname)

                tmp_module = hdict['new_module']
                tmp_name   = hdict['new_name']
                hdict.pop('new_module', None)
                hdict.pop('new_name', None)

                pyfile.initPlugin()

                hdict['new_module'] = tmp_module
                hdict['new_name']   = tmp_name

                self.restart(_("Revert to original hoster plugin"))

            else:
                raise Fail(e)


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)


    def handle_free(self, pyfile):
        if self.premium:
            raise NotImplementedError
        else:
            self.fail(_("Required premium account not found"))
