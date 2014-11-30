import re
from module.plugins.Crypter import Crypter

class Go4Up(Crypter):
    __name__ = 'Go4Up'
    __type__ = 'crypter'
    __version__ = '0.1'
    __pattern__ = r'^http://go4up.com/dl/[0-9a-f]{12}$'
    __config__ = [('preference_order', 'str',
                   'preference order (comma-seperated) names from http://go4up.com/misc/mirrorlist',
                   '1fichier, filecould')]
    __description__ = '''Go4Up decrypter'''
    __license__ = 'GPLv3'
    __authors__ = [('rlindner81', 'rlindner81@gmail.com')]

    # names from http://go4up.com/misc/mirrorlist
    HOSTERS = {
        'filecloud':    {'suffix': '/20', 're': r'(http://filecloud\.io/........)'},
        'zippyshare':   {'suffix': '/42', 're': r'(http://www..\.zippyshare\.com/v/......../file\.html)'},
        '1fichier':     {'suffix': '/43', 're': r'(http://..........\.1fichier\.com)'},
        '180upload':    {'suffix': '/45', 're': r'(http://180upload\.com/............)'},
        'billionuploads': {'suffix': '/47', 're': r'(http://billionuploads\.com/............)'},
        'hugefiles':    {'suffix': '/56', 're': r'(http://hugefiles\.net/............)'},
        'solidfiles':   {'suffix': '/61', 're': r'(http://www\.solidfiles\.com/d/........../)'},
    }
    DEADLINK = 'Error link not available'

    def decrypt(self, pyfile):
        # iterate over hosters in preference order
        preference_order = map(lambda x: x.strip(), self.getConfig("preference_order").split(','))
        for i in range(len(preference_order)):
            name = preference_order[i]
            if not name in self.HOSTERS:
                self.logWarning('Hoster %s is unknown' % name)
                continue

            # get the html page where the target url is
            hoster = self.HOSTERS[name]
            source_url = pyfile.url.replace('/dl/', '/rd/') + hoster['suffix']
            source_html = self.load(source_url, decode=True)

            # match the hoster's re
            match = re.search(hoster['re'], source_html)
            if match:
                target_url = match.group(1)
                pypackage = self.pyfile.package()
                self.packages.append((pypackage.name, (target_url, ), pypackage.folder))
                return

            # if match failed, check that it was a normal deadlink
            if re.search(self.DEADLINK, source_html):
                self.logDebug('Hoster %s does not host this file' % name)
                continue

            # if match failed and it was not a deadlink, the re is probably wrong
            self.logError('Deadlink or Hoster %s regular expression is probably wrong' % name)

        # if no prefered hoster matched, we conclude the file is offline
        self.offline()