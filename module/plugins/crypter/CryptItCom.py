# -*- coding: utf-8 -*-

import tempfile
import re
from os import remove
import os.path

from time import time
from module.plugins.Crypter import Crypter


class CryptItCom(Crypter):
    __name__ = "CryptItCom"
    __type__ = "container"
    __pattern__ = r"http://[\w\.]*?crypt-it\.com/(s|e|d|c)/[\w]+"
    __version__ = "0.1"
    __description__ = """Crypt.It.com Container Plugin"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")
        
    def __init__(self, parent):
        Crypter.__init__(self, parent)
        self.parent = parent
    
    def file_exists(self):
        html = self.load(self.parent.url)
        if r'<div class="folder">Was ist Crypt-It</div>' in html:
            return False
        return True        
    
    def proceed(self, url, location):
        repl_pattern = r"/(s|e|d|c)/"
        url = re.sub(repl_pattern, r"/d/", url)
        
        # download ccf
        file_name = os.path.join(tempfile.gettempdir(), "pyload_tmp_%d.ccf"%time())
        file_name = self.req.download(url, file_name)
        if file_name == "redir.ccf":
            remove(file_name)
            raise Exception, _("File not found")

        # and it to package
        self.links = [file_name]
        