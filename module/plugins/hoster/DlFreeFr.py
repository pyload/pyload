#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns
from module.common.json_layer import json_loads

import pycurl
from module.network.Browser import Browser

class DlFreeFr(SimpleHoster):
    __name__ = "DlFreeFr"
    __type__ = "hoster"
    __pattern__ = r"http://dl\.free\.fr/([a-zA-Z0-9]+|getfile\.pl\?file=/[a-zA-Z0-9]+)"
    __version__ = "0.23"
    __description__ = """dl.free.fr download hoster"""
    __author_name__ = ("the-razer", "zoidberg", "Toilal")
    __author_mail__ = ("daniel_ AT gmx DOT net", "zoidberg@mujmail.cz", "toilal.dev@gmail.com")
       
    FILE_NAME_PATTERN = r"Fichier:</td>\s*<td[^>]*>(?P<N>[^>]*)</td>"
    FILE_SIZE_PATTERN = r"Taille:</td>\s*<td[^>]*>(?P<S>[\d.]+[KMG])o"
    FILE_OFFLINE_PATTERN = r"Erreur 404 - Document non trouv|Fichier inexistant|Le fichier demand&eacute; n'a pas &eacute;t&eacute; trouv&eacute;"
    #FILE_URL_PATTERN = r'href="(?P<url>http://.*?)">T&eacute;l&eacute;charger ce fichier'   
    
    ADYOULIKE_INPUT_PATTERN = r'Adyoulike.create\((.*?)\);'
    ADYOULIKE_CALLBACK = r'Adyoulike.g._jsonp_5579316662423138'
    ADYOULIKE_CHALLENGE_PATTERN =  ADYOULIKE_CALLBACK + r'\((.*?)\)'
    
    class CustomBrowser(Browser):
        def __init__(self, bucket=None, options={}):
            Browser.__init__(self, bucket, options)
        
        def load(self, *args, **kwargs):        
            self.http.c.setopt(pycurl.CUSTOMREQUEST, "GET")
            return Browser.load(self, *args, **kwargs)
        
    def setup(self):
        self.multiDL = True
        self.limitDL = 5
        self.resumeDownload = True
        self.chunkLimit = 1        

    def init(self):
        factory = self.core.requestFactory
        self.req = DlFreeFr.CustomBrowser(factory.bucket, factory.getOptions())
                
    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.FILE_URL_REPLACEMENTS)
        valid_url = pyfile.url
        headers = self.load(valid_url, decode = False, cookies = False, just_header = True)
        
        self.html = None
        if headers.get('code') == 302:
            valid_url = headers.get('location')
            headers = self.load(valid_url, decode = False, cookies = False, just_header = True)
        
        if headers.get('code') == 200:
            content_type = headers.get('content-type')
            if content_type and content_type.startswith("text/html"):
                # Undirect acces to requested file, with a web page providing it (captcha)
                self.html = self.load(valid_url, decode = False, cookies = self.SH_COOKIES)
                self.handleFree()
            else:
                # Direct access to requested file for users using free.fr as Internet Service Provider. 
                self.download(valid_url)   
        elif headers.get('code') == 404:
            self.offline()
        else:
            self.fail("Invalid return code: " + headers.get('code'))
            
    def handleFree(self):
        if "Trop de slots utilis&eacute;s" in self.html:
            self.retry(300)
            
        adyoulike_data_string = None
        found = re.search(self.ADYOULIKE_INPUT_PATTERN, self.html)
        if found:
            adyoulike_data_string = found.group(1)
        else:
            self.fail("Can't retrieve addyoulike input data")
            
        action, inputs = self.parseHtmlForm('action="getfile.pl"')
            
        ayl_engine = "adyoulike"
        
        ayl_data = json_loads(adyoulike_data_string) #{"adyoulike":{"key":"P~zQ~O0zV0WTiAzC-iw0navWQpCLoYEP"},"all":{"element_id":"ayl_private_cap_92300","lang":"fr","env":"prod"}}
        ayl_key = ayl_data[ayl_engine]["key"]
        ayl_lang = ayl_data["all"]["lang"]
        ayl_env = ayl_data["all"]["env"]
        
        res = self.load(r'http://api-ayl.appspot.com/challenge?key=%(ayl_key)s&env=%(ayl_env)s&callback=%(callback)s' % {"ayl_key": ayl_key, "ayl_env": ayl_env, "callback": self.ADYOULIKE_CALLBACK})                  
        found = re.search(self.ADYOULIKE_CHALLENGE_PATTERN, res)
        challenge_string = None
        if found:
            challenge_string = found.group(1)
        else:
            self.fail("Invalid addyoulike challenge")
        challenge_data = json_loads(challenge_string)
        """
        Adyoulike.g._jsonp_5579316662423138({"translations":{"fr":{"instructions_visual":"Recopiez « Soonnight » ci-dessous :"}},"site_under":true,"clickable":true,"pixels":{"VIDEO_050":[],"DISPLAY":[],"VIDEO_000":[],"VIDEO_100":[],"VIDEO_025":[],"VIDEO_075":[]},"medium_type":"image/adyoulike","iframes":{"big":"<iframe src=\"http://www.soonnight.com/campagn.html\" scrolling=\"no\" height=\"250\" width=\"300\" frameborder=\"0\"></iframe>"},"shares":{},"id":256,"token":"e6QuI4aRSnbIZJg02IsV6cp4JQ9~MjA1","formats":{"small":{"y":300,"x":0,"w":300,"h":60},"big":{"y":0,"x":0,"w":300,"h":250},"hover":{"y":440,"x":0,"w":300,"h":60}},"tid":"SqwuAdxT1EZoi4B5q0T63LN2AkiCJBg5"})
        """
        ayl_response = None
        try:
            instructions_visual = challenge_data["translations"][ayl_lang]["instructions_visual"]
            # We have an instructions visual. Easy :)
            found = re.search(u".*«(.*)».*", instructions_visual)
            if found:
                ayl_response = found.group(1).strip()
            else:
                self.fail("Can't parse instructions visual")
        except KeyError:
            self.fail("No instructions visual")
        
        ayl_tid = challenge_data["tid"]
        ayl_token = challenge_data["token"]
        
        res = self.load("http://api-ayl.appspot.com/resource?token=%(ayl_token)s&env=%(ayl_env)s" % {"ayl_token": ayl_token, "ayl_env": ayl_env})       
        
        inputs.update( {"_ayl_captcha_engine" : ayl_engine, 
                        "_ayl_env" :    ayl_env,
                        "_ayl_tid" :    ayl_tid,
                        "_ayl_token_challenge" :    ayl_token} )
                
        self.download("http://dl.free.fr/getfile.pl", post = inputs)
                
getInfo = create_getInfo(DlFreeFr)   
