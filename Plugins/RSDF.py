#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import re
import time
import binascii
import base64
import sys

from Plugin import Plugin
from time import time

class RSDF(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        self.plugin_name = "RSDF"
        self.plugin_pattern = r".*\.rsdf"
        self.plugin_type = "container"
        self.plugin_config = {}
        pluginProp = {}
        pluginProp ['name'] = "RSDF"
        pluginProp ['version'] = "0.1"
        pluginProp ['format'] = "*.py"
        pluginProp ['description'] = """RSDF Plugin"""
        pluginProp ['author'] = "RaNaN"
        pluginProp ['author_email'] = "RaNaN@pyload.org"
        self.pluginProp = pluginProp
        self.parent = parent
        self.multi_dl = True
        self.links = []
        
    def file_exists(self):
        """ returns True or False 
        """
        return True

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        return self.parent.url
    
    def __call__(self):
        return self.plugin_name

    def proceed(self, url, location):
        try:
            from Crypto.Cipher import AES
            
            infile = url.replace("\n","")
            Key = binascii.unhexlify('8C35192D964DC3182C6F84F3252239EB4A320D2500000000')
    
            IV = binascii.unhexlify('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
            IV_Cipher = AES.new(Key,AES.MODE_ECB)
            IV = IV_Cipher.encrypt(IV)
    
            obj = AES.new(Key,AES.MODE_CFB,IV)
    
            rsdf = open(infile,'r')
    
            data = rsdf.read()
            data = binascii.unhexlify(''.join(data.split()))
            data = data.splitlines()
    
            for link in data:
                link = base64.b64decode(link)
                link = obj.decrypt(link)
                decryptedUrl = link.replace('CCF: ','')
                self.links.append(decryptedUrl)
    
            rsdf.close()
            print self.links
        
        except:
            print "Kein Crypto installiert, RSDF Plugin kann nicht genutzt werden"
