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
        plugin_config = {}
        plugin_config['name'] = "RSDF"
        plugin_config['type'] = "container"
        plugin_config['pattern'] = r".*\.rsdf"
        plugin_config['version'] = "0.2"
        plugin_config['description'] = """RSDF Container Decode Plugin"""
        plugin_config['author_name'] = ("RaNaN", "spoob")
        plugin_config['author_mail'] = ("RaNaN@pyload.org", "spoob@pyload.org")
        self.plugin_config = plugin_config
        self.parent = parent
        self.multi_dl = True
        self.links = []
        
    def file_exists(self):
        """ returns True or False 
        """
        return True
    
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
