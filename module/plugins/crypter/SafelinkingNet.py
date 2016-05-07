# -*- coding: utf-8 -*-

import re

from module.plugins.internal.misc import json
from module.network.HTTPRequest import BadHeader
from module.plugins.internal.Crypter import Crypter
from module.plugins.captcha.SolveMediaJson import SolveMediaJson


class SafelinkingNet(Crypter):
    __name__    = "SafelinkingNet"
    __type__    = "crypter"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?safelinking\.net/(([pd])/)?\w+'
    __config__  = [("activated"         , "bool"          , "Activated"                       , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available", True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"  , "Default")]

    __description__ = """Safelinking.net decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("quareevo", "quareevo@arcor.de"),("tbsn","tbsnpy_github@gmx.de")]


    SOLVEMEDIA_PATTERN = "solvemediaApiKey = '([\w\-.]+)';"

    SAFELINKING_SOLVEMEDIA_KEY = "OZ987i6xTzNs9lw5.MA-2Vxbc-UxFrLu"


    def json_response(self, url, hash, challenge, response, multipart=False):
        
        self.req.clearHeaders()
        
        self.req.putHeader("User-Agent", "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/38.0")
        self.req.putHeader("Accept", "application/json, text/plain, */*")
        self.req.putHeader("Accept-Language", "en-US,en;q=0.5")
        self.req.putHeader("Accept-Encoding", "gzip, deflate, br")
        self.req.putHeader("Content-Type" , "application/json;charset=utf-8")
        
        post = json.dumps({'answer': response,
                           'challengeId' : challenge ,
                           'hash': hash ,
                           'type' : '0'})

        res = None
        try:
            html = self.load(url,
                             post=post,
                             decode=False)
                        
            self.log_debug("Response answer: ")
            self.log_debug(html)

            res = json.loads(html)

        except BadHeader, e:
            self.log_debug(e)


        return res


    def decrypt(self, pyfile):
        
        self.log_debug("Self:")
        self.log_debug(self)
        
        url = pyfile.url
        
        self.log_debug("Link name: %s" % self.pyfile.name )

        if re.match(self.__pattern__, url).group(1) == "d":

            header = self.load(url, just_header=True)
            if 'location' in header:
                self.links = [header.get('location')]
            else:
                self.error(_("Couldn't find forwarded Link"))

        else:
            postData = {"post-protect": "1"}

            # This sets the referrer for further calls
            self.data = self.load(url)
            
            self.log_debug("SafelinkingNet() first page: %s" % self.data)
            
            if "link-password" in self.data:
                postData['link-password'] = self.get_password()
            
            
            if "ajaxSetup" in self.data:
                
                # Use static key for now
                captchaKey = SafelinkingNet.SAFELINKING_SOLVEMEDIA_KEY
                captcha = SolveMediaJson(pyfile)
                captchaProvider = "Solvemedia"

                response, challenge = captcha.challenge(captchaKey)
                
                json_res = self.json_response( "https://safelinking.net/v1/captcha" , self.pyfile.name , challenge, response, multipart=False)
                
                if( None == json_res ):
                    self.error("No valid JSON response")
                elif( "message" in json_res ):
                    self.log_info("Message: %s" % json_res['message'] )
                    self.retry(wait=10, msg=json_res['message'])
                elif( "links" in json_res ):
                    for link in json_res['links']:
                        self.log_debug("Url: ")
                        self.log_debug(link['url'])
                        self.links.append(link['url'])
                else:
                    self.log_debug("Unexpected response")
