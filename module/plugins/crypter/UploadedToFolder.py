# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class UploadedToFolder(SimpleCrypter):
    __name__ = "UploadedToFolder"
    __type__ = "crypter"
    __version__ = "0.3"

    __pattern__ = r'http://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/(?P<id>\w+)'

    __description__ = """UploadedTo decrypter plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    PLAIN_PATTERN = r'<small class="date"><a href="(?P<plain>[\w/]+)" onclick='
    TITLE_PATTERN = r'<title>(?P<title>[^<]+)</title>'


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)

        package_name, folder_name = self.getPackageNameAndFolder()

        m = re.search(self.PLAIN_PATTERN, self.html)
        if m:
            plain_link = 'http://uploaded.net/' + m.group('plain')
        else:
            self.fail('Parse error - Unable to find plain url list')

        self.html = self.load(plain_link)
        package_links = self.html.split('\n')[:-1]
        self.logDebug('Package has %d links' % len(package_links))

        self.packages = [(package_name, package_links, folder_name)]
