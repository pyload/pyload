import re
from module.plugins.Hoster import Hoster

class ImgurCom(Hoster):
  __name__ = "ImgurCom"
  __type__ = "hoster"
  __version__ = "0.1"
  __description__ = """Imgur.com hoster plugin"""
  __pattern__ = r"http[s]?://imgur\.com/\w{7}"
  __config__ = []
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"
 
  def process(self, pyfile):
    html = self.load(pyfile.url)
    
    filetypes="(?:jpeg|jpg|png|gif|apng)"
    
    single_url = re.search(r'i\.imgur\.com/\w{7}\.'+filetypes, html)
   
    if single_url:
      #complete downloadable url
      single_url="http://"+single_url.group(0)
      #parse name for file
      pyfile.name = re.search(r'\w{7}\.'+filetypes, single_url).group(0)
      self.download(single_url)
    else:
      self.logInfo('No urls found')
