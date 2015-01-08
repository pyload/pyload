# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class EasybytezCom(MultiHook):
    __name__    = "EasybytezCom"
    __type__    = "hook"
    __version__ = "0.07"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """EasyBytez.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def getHosters(self):
        user, data = self.account.selectAccount()

        try:
            req  = self.account.getAccountRequest(user)
            page = req.load("http://www.easybytez.com")

            hosters = re.search(r'</textarea>\s*Supported sites:(.*)', page).group(1).split(',')

        except Exception, e:
            self.logWarning(_("Unable to load supported hoster list, using last known"))
            self.logDebug(e)

            hosters = ["bitshare.com", "crocko.com", "ddlstorage.com", "depositfiles.com", "extabit.com", "hotfile.com",
                       "mediafire.com", "netload.in", "rapidgator.net", "rapidshare.com", "uploading.com", "uload.to",
                       "uploaded.to"]
        finally:
            return hosters
