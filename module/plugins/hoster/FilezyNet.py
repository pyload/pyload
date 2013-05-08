# -*- coding: utf-8 -*-
import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import html_unescape
from module.network.RequestFactory import getURL 

class FilezyNet(SimpleHoster):
  __name__ = "FilezyNet"
  __type__ = "hoster"
  __version__ = "0.1"
  __pattern__ = r"http://filezy.net/.*/.*.html"
  __description__ = """filezy.net hoster plugin"""

  FILE_INFO_PATTERN = r'<p>Download: <span>(?P<N>[^<]+)</span> <span class="plansize">(?P<S>[^<]+)</span>'
  FILE_OFFLINE_PATTERN = r'<h2>File Not Found</h2>'

  def setup(self):
    self.resumeDownload = True
    self.multiDL = False

  def handleFree(self):
    # Define search patterns
    op_pattern = '<input type="hidden" name="op" value="(.*)">'
    id_pattern = '<input type="hidden" name="id" value="(.*)">'
    fn_pattern = '<input type="hidden" name="fname" value="(.*)">'
    re_pattern = '<input type="hidden" name="referer" value="(.*)">'
    ul_pattern = '<input type="hidden" name="usr_login" value="(.*)">'
    rand_pattern = '<input type="hidden" name="rand" value="(.*)">'
    link_pattern = '<a href="(.*)" class="btn-video">Download File</a>'

    # Get HTML source
    self.logDebug("Getting first HTML source")
    html = self.load(self.pyfile.url)
    self.logDebug(" > Done")

    op_val = re.search(op_pattern, html).group(1)
    id_val = re.search(id_pattern, html).group(1)
    fn_val = re.search(fn_pattern, html).group(1)
    re_val = re.search(re_pattern, html).group(1)
    ul_val = re.search(ul_pattern, html).group(1)

    # Debug values
    self.logDebug(" > Op " + op_val)
    self.logDebug(" > Id " + id_val)
    self.logDebug(" > Fname " + fn_val)
    self.logDebug(" > Referer " + re_val)
    self.logDebug(" > User Login " + ul_val)

    # Create post data
    post_data = {"op" : op_val, "usr_login" : ul_val, "id" : id_val, "fname" : fn_val, "referer" : re_val, "method_free" : "+Free+Download"}

    # Post and get new HTML source
    self.logDebug("Getting second HTML source")
    html = self.load(self.pyfile.url, post = post_data, decode=True)
    self.logDebug(" > Done")

    # Retrieve data
    if re.search(op_pattern, html) is not None:
      op_val = re.search(op_pattern, html).group(1)
    else:
      self.retry(3, 10, "Second html: no op found!!")

    if re.search(id_pattern, html) is not None:
      id_val = re.search(id_pattern, html).group(1)
    else:
      self.retry(3, 10, "Second html: no id found!!")

    if re.search(rand_pattern, html) is not None:
      rand_val = re.search(rand_pattern, html).group(1)
    else:
      self.retry(3, 10, "Second html: no rand found!!")

    re_val = self.pyfile.url

    # Debug values
    self.logDebug(" > Op " + op_val)
    self.logDebug(" > Id " + id_val)
    self.logDebug(" > Rand " + rand_val)
    self.logDebug(" > Referer " + re_val)

    self.setWait(31)
    self.wait()

    # Create post data
    post_data = {"op" : op_val, "id" : id_val, "rand" : rand_val, "referer" : re_val, "method_free" : "+Free+Download", "method_premium" : "", "down_direct" : "1"}

    # Post and get new HTML source
    self.logDebug("Getting third HTML source")
    html = self.load(self.pyfile.url, post = post_data, decode=True)
    self.logDebug(" > Done")

    # Get link value
    if re.search(link_pattern, html) is not None:
      link_val = re.search(link_pattern, html).group(1)
      self.logDebug(" > Link " + link_val)
      self.download(link_val)
    else:
      self.logDebug("No link found!!")
      self.retry(3, 10, "No link found!!")

getInfo = create_getInfo(FilezyNet)
