# -*- coding: utf-8 -*-

import re

from module.plugins.internal.misc import json
from module.network.HTTPRequest import BadHeader
from module.plugins.internal.Crypter import Crypter
from module.plugins.captcha.SolveMedia import SolveMedia


class SafelinkingNet(Crypter):
    __name__    = "SafelinkingNet"
    __type__    = "crypter"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?safelinking\.net/(?P<link_type>[pd]/)?\w+'
    __config__  = [("activated"         , "bool"          , "Activated"                       , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available", True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"  , "Default")]

    __description__ = """Safelinking.net decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("quareevo", "quareevo@arcor.de"),("tbsn","tbsnpy_github@gmx.de")]

    # Safelinking seems to use a static SolveMedia key
    SAFELINKING_SOLVEMEDIA_KEY = "OZ987i6xTzNs9lw5.MA-2Vxbc-UxFrLu"
    
    # Safelinking url that handles the captcha response
    SAFELINKING_CAPTCHA_JSON_URL = "https://safelinking.net/v1/captcha"


    def json_response(self, hash, challenge, response):

        self.req.clearHeaders()
        self.req.putHeader("Accept", "application/json")
        self.req.putHeader("Accept-Encoding", "gzip, deflate, br")
        self.req.putHeader("Content-Type" , "application/json")
                
        if( self.package_password ):
            post = json.dumps({'answer': response, 'challengeId' : challenge, 
                               'hash': hash, 'type' : '0', 'password' : self.package_password  })
        else:
            post = json.dumps({'answer': response, 'challengeId' : challenge, 'hash': hash, 'type' : '0'})

        res = None
        try:
            html = self.load( SafelinkingNet.SAFELINKING_CAPTCHA_JSON_URL , post=post)
            res = json.loads(html)

        except BadHeader, e:
            self.log_debug(e)

        return res


    def decrypt(self, pyfile):
        
        url = pyfile.url

        self.package_password = self.get_password()
        
        if( self.package_password ):
            self.log_debug("Using package password %s" % self.package_password )
        
        # Process direct links
        if re.match(self.__pattern__, url).group('link_type') == "d/":
            header = self.load(url, just_header=True)

            if 'location' in header:
                self.links = [header.get('location')]

            else:
                self.error(_("Couldn't find forwarded Link"))
                
        # Process protected links
        else:
            # Load Safelinking site 
            # This sets the referrer for further calls
            self.data = self.load(url)
            #self.log_debug("SafelinkingNet() first page: %s" % self.data)

            
            if "ajaxSetup" in self.data:
                # Use static key for now
                captchaKey = SafelinkingNet.SAFELINKING_SOLVEMEDIA_KEY

                # Retreive and solve captcha
                captcha = SolveMedia(pyfile)
                response, challenge = captcha.challenge(key=captchaKey)
                
                # Send response to Safelinking
                json_res = self.json_response( self.pyfile.name , challenge, response)
                
                # Evaluate response
                if( None == json_res ):
                    self.fail("No valid JSON response")
                    
                # Response: Wrong password
                elif( "passwordFail" in json_res ):
                                        
                    if( self.package_password ):
                        self.fail("Wrong password: \"%s\"" % self.package_password )
                    else:
                        self.fail(_("Please enter the password in package section and try again"))

                # Response: Error message
                elif( "message" in json_res ):
                    self.log_info("Message: %s" % json_res['message'] )
                    self.retry(wait=1, msg=json_res['message'])

                # Response: Links
                elif( "links" in json_res ):
                    for link in json_res['links']:
                        self.links.append(link['url'])
                else:
                    self.fail("Unexpected JSON response")
