import re
from module.plugins.Crypter import Crypter

class FilerNetFolder(Crypter):
  __name__ = "FilerNetFolder"
  __type__ = "crypter"
  __version__ = "0.1"
  __description__ = """Filer.net decrypter plugin"""
  __pattern__ = r"http[s]?://filer\.net/folder/\w{16}"
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
        parsed_urls.add("http://filer.net/get/"+re.search(r'\w{16}', url).group(0)) 
      
      #determine a name for the newly added package
      name = "filerNet_" + re.search(r'filer\.net/folder/(\w{16})', pyfile.url).group(1)
      self.logDebug('Determined name for package: '+name)
      
      self.packages.append((name, list(parsed_urls), name))
    else:
      self.logInfo('No urls found')
