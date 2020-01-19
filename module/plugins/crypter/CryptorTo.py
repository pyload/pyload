# -*- coding: utf-8 -*-

import binascii
import os
import re

#from bs4 import BeautifulSoup as Soup
import requests

import Crypto.Cipher.AES

from module.plugins.internal.Crypter import Crypter
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.misc import fsjoin

class CryptorTo(Crypter):
    __name__    = "CryptorTo"
    __type__    = "crypter"
    __version__ = "0.01"
    __status__  = "testing"

    __pattern__ = r'http://cryptor.to/folder/(?P<ID>.+)'
    __config__  = [("activated"         , "bool"          , "Activated"                       , True     )]

    __description__ = """CryptorTo decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("4Christopher", "4Christopher@gmx.de")]

    OFFLINE_TOKEN = r'<h3 class="text-center" style="color:#01bf86">Ordner nicht'

    PASSWORD_TOKEN = r'folder_access_password_check'
    PASSWORD_ERROR_BROKEN = r'Bitte gebe das g'

    CNL2_JK_KEY = r"jk':\s'function\sf\(\)\s\{\sreturn\s\\'(.*)\\';"
    CNL2_CRYPTED_KEY = "crypted': '(.*?)',"

    CAPTCHA_PATTERN = r'class="g-recaptcha"'

    SITE_KEY = '6Lc3CyQTAAAAANsQNkMX2C7mT5K4r7FI82P3P2U1'

    def decrypt(self, pyfile):

        self.data = self.load(pyfile.url)

        #: Check for online
        if not self.is_online():
            self.offline()

        # handle_captcha
        self.handle_captcha(pyfile)

        if self.is_password_protected():
            self.unlock_password_protection(pyfile.url)

        links=self.handle_CNL2Links()
        links=set(links)
        if links:
            self.packages = [(self.info['name'], links, self.info['name'])]

    def is_online(self):
        if self.OFFLINE_TOKEN in self.data:
            self.log_debug("File not found")
            return False
        return True


    def is_captcha_protected(self):
        if self.CAPTCHA_TOKEN in self.data:
            self.log_debug("Links are captcha protected")
            return True
        return False



    def is_password_protected(self):
        if self.PASSWORD_TOKEN in self.data:
            self.log_debug("Links are password protected")
            return True


    def unlock_password_protection(self,url):
        password = self.get_password()
        self.log_debug("Submitting password [%s] for protected links" % password)

        if password:
            passwd_data = {'folder_access[password_check]': password, 'folder_access[submit]': ''}
            self.data = self.load(url, post=passwd_data)
            fail=re.findall(self.PASSWORD_ERROR_BROKEN, self.data)
            if fail:
                self.fail(_("Wrong password"))
        else:
            self.fail(_("Wrong password"))



    def handle_CNL2Links(self):
        self.log_debug("Search for CNL2 links")
        pack_links = []
        try:
            (vcrypted, vjk) = self._get_cipher_params(self.data)
            if vjk is not None:
                for (crypted, jk) in zip(vcrypted, vjk):
                    pack_links.extend(self._get_links(crypted, jk))
        except Exception:
            self.log_debug("Unable to decrypt CNL2 links", trace=True)

        return pack_links


    def _get_cipher_params(self, data):
        #: Get jk
        vjk = re.findall(self.CNL2_JK_KEY,data) # % self.CNL2_JK_KEY

        vcrypted = re.findall(self.CNL2_CRYPTED_KEY, data)

        #: Log and return
        self.log_debug("Detected %d crypted blocks" % len(vcrypted))
        return vcrypted, vjk


    def _get_links(self, crypted, jk):
        key = binascii.unhexlify(jk)

        #: Decrypt
        Key = key
        IV = key
        obj = Crypto.Cipher.AES.new(Key, Crypto.Cipher.AES.MODE_CBC, IV)
        text = obj.decrypt(crypted.decode('base64'))

        #: Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        #: Log and return
        self.log_debug("Package has %d links" % len(links))
        return links


    def handle_captcha(self, pyfile):
        if re.search(self.CAPTCHA_PATTERN, self.data):
            #protectedPage = Soup(requests.get(pyfile.url).text, 'html5lib')
            #s = protectedPage.find('input', {'name': 's'})['value']
            # self.captcha = ReCaptcha(pyfile)
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()
            recaptchaVerificationToken = recaptcha.challenge(key=self.SITE_KEY, version=2)
            unlockedPage = requests.post(
                pyfile.url,
                data={
                    'g-recaptcha-response': recaptchaVerificationToken,
                    's': s,
                    'action': 'Download',
                    'newcap': 'true'
                }
            )
            unlockedPage = Soup(unlockedPage.text, 'html5lib')

            '''recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()

            if captcha_key:
                self.captcha = recaptcha

                try:
                    response, challenge = recaptcha.challenge(captcha_key)

                except Exception:
                    self.retry_captcha()

                self.site_with_links = self.load(self.pyfile.url,
                                                 post={'g-recaptcha-response': response})

        if re.search(self.CAPTCHA_PATTERN, self.site_with_links):
            self.retry_captcha()'''
