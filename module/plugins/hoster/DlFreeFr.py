# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DlFreeFr(SimpleHoster):
    __name__    = "DlFreeFr"
    __type__    = "hoster"
    __version__ = "0.35"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?dl\.free\.fr/(getfile\.pl\?file=/|[a-z])(?P<ID>\w+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Dl.free.fr hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'Fichier:</td>\s*<td.*?>(?P<N>[^>]*)</td>'
    SIZE_PATTERN    = r'Taille:</td>\s*<td.*?>(?P<S>[\d.,]+)(?P<U>\w+)'
    OFFLINE_PATTERN = r'>ERREUR 404|Fichier inexistant'


    def setup(self):
        self.resume_download = True
        self.multiDL         = True
        self.limitDL         = 5
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        self.download("http://dl.free.fr/getfile.pl",
                      post={'file': '/' + self.info['pattern']['ID'],
                            'send': "Valider+et+télécharger+le+fichier"})


getInfo = create_getInfo(DlFreeFr)
