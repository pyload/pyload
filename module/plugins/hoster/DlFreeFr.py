#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.ReCaptcha import ReCaptcha

class DlFreeFr(SimpleHoster):
    __name__ = "DlFreeFr"
    __type__ = "hoster"
    __pattern__ = r"http://dl\.free\.fr/([a-zA-Z0-9]+|getfile\.pl\?file=/[a-zA-Z0-9]+)"
    __version__ = "0.22"
    __description__ = """dl.free.fr download hoster"""
    __author_name__ = ("the-razer", "zoidberg")
    __author_mail__ = ("daniel_ AT gmx DOT net", "zoidberg@mujmail.cz")
       
    FILE_NAME_PATTERN = r"Fichier:</td>\s*<td[^>]*>(?P<N>[^>]*)</td>"
    FILE_SIZE_PATTERN = r"Taille:</td>\s*<td[^>]*>(?P<S>[\d.]+[KMG])o"
    FILE_OFFLINE_PATTERN = r"Erreur 404 - Document non trouv|Fichier inexistant|Le fichier demand&eacute; n'a pas &eacute;t&eacute; trouv&eacute;"
    #FILE_URL_PATTERN = r'href="(?P<url>http://.*?)">T&eacute;l&eacute;charger ce fichier'
    
    RECAPTCHA_KEY_PATTERN = r'"recaptcha":{"key":"(.*?)"}'
    
    def setup(self):
        self.multiDL = True
        self.limitDL = 5
        self.resumeDownload = True
        self.chunkLimit = 1

    def handleFree(self):
        if "Trop de slots utilis&eacute;s" in self.html:
            self.retry(300)
            
        recaptcha_key = '6Lf-Ws8SAAAAAAO4ND_KCqpZzNZQKYEuOROs4edG'
        found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
        if found: recaptcha_key = found.group(1)
        
        action, inputs = self.parseHtmlForm('action="getfile.pl"')
        inputs.update( {"_ayl_captcha_engine" : "recaptcha", 
                        "_ayl_env" :	"prod",
                        "_ayl_tid" :	"undefined",
                        "_ayl_token_challenge" :	"undefined"} )
        
        recaptcha = ReCaptcha(self)
        inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(recaptcha_key)
        
        self.download("http://dl.free.fr/getfile.pl", post = inputs)

getInfo = create_getInfo(DlFreeFr)   
