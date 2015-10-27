# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class FreeWayMe(MultiHoster):
    __name__    = "FreeWayMe"
    __type__    = "hoster"
    __version__ = "0.22"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?free-way\.(bz|me)/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """FreeWayMe multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def setup(self):
        self.resume_download = False
        self.multiDL        = self.premium
        self.chunk_limit     = 1


    def handle_premium(self, pyfile):
        user, data = self.account.select()

        for _i in xrange(5):
            #: Try it five times
            header = self.load("http://www.free-way.bz/load.php",  #@TODO: Revert to `https` in 0.4.10
                               get={'multiget': 7,
                                    'url'     : pyfile.url,
                                    'user'    : user,
                                    'pw'      : self.account.get_login('password'),
                                    'json'    : ""},
                               just_header=True)

            if 'location' in header:
                headers = self.load(header.get('location'), just_header=True)
                if headers['code'] == 500:
                    #: Error on 2nd stage
                    self.log_error(_("Error [stage2]"))
                else:
                    #: Seems to work..
                    self.download(header.get('location'))
                    break
            else:
                #: Error page first stage
                self.log_error(_("Error [stage1]"))

            #@TODO: handle errors


getInfo = create_getInfo(FreeWayMe)
