import re
from module.plugins.Crypter import Crypter

class FilerNetFolder(Crypter):
  __name__ = "FilerNetFolder"
  __type__ = "crypter"
  __version__ = "0.1"
  __description__ = """Filer.net decrypter plugin"""
  __pattern__ = r"http[s]?://filer\.net/folder/(?P<ID>\w{16})"
  __config__ = []
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"
  
  def decrypt(self, pyfile):
    
    html = self.load(pyfile.url)
    
    raw_urls = re.findall(r'(\w{16})"', html)
    
    if raw_urls:
      parsed_urls = set()
      
      #Iterate over raw_urls and add add the set - uniqizes the urls automatically
      for i, url in enumerate(raw_urls):
        temp_url = "http://filer.net/get/"+re.search(r'\w{16}', url).group(0)
        self.logDebug(temp_url)
        parsed_urls.add(temp_url)
     
      #determine a name for the newly added package
      name = "filerNet_" + re.search(__pattern__, pyfile.url).group("ID")
      self.logDebug('Determined name for package: '+name)
      
      self.packages.append((name, list(parsed_urls), name))
    else:
      self.logInfo('No urls found')
