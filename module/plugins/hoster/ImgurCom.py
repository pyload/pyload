import re
from module.plugins.Hoster import Hoster
import module.PyFile

class ImgurCom(Hoster):
  __name__ = "ImgurCom"
  __type__ = "hoster"
  __version__ = "0.1"
  __description__ = """Imgur.com hoster plugin"""
  __pattern__ = r"http[s]?://imgur\.com/*"
  __config__ = []
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"
 
  def process(self, pyfile):
    html = self.load(pyfile.url)
   
    parsed_urls = re.findall(r'i\.imgur\.com\/\w{7}\.\w{3,4}', html)
   
    if parsed_urls:
      #for now only the last file will show up in queue - it still downloads all files
      for single_url in parsed_urls:
        single_url="http://"+single_url
        pyfile.name = re.search(r'\w{7}\.\w{3,4}', single_url).group(0)
        self.download(single_url)
    else:
      self.logInfo('No urls found')
