import re
from module.plugins.internal.SimpleCrypter import SimpleCrypter

class FilerNetFolder(SimpleCrypter):
  __name__ = "FilerNetFolder"
  __type__ = "crypter"
  __version__ = "0.2"
  __description__ = """Filer.net decrypter plugin"""
  __pattern__ = r"https?://filer\.net/folder/\w{16}"
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"

  LINK_PATTERN = r'/get/\w{16}'
  TITLE_PATTERN = r'<h3>(?P<title>.+) - <small'

  def getLinks(self):
    f: lambda url: "http:filer.net/get/" + re.search(r'\w{16}', url).group(0)
    return list(set(map(f, re.finall(self.LINK_PATTERN, self.html))))
