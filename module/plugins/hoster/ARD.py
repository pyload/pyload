
import re

from module.plugins.internal.SimpleHoster import SimpleHoster


class ARD(SimpleHoster):
  __name__    = "ARD"
  __type__    = "hoster"
  __version__ = "0.01"
  __status__  = "testing"
  __pattern__ = r'https?://(?:www\.)?ardmediathek\.de'
  __description__ = """ARD hoster plugin"""
  __license__     = "GPLv3"
  __authors__     = [("igel", "")]

  OFFLINE_PATTERN      = r'Seite nicht gefunden'
  DOC_ID_PATTERN       = r'description.*?documentId=(\d+)'
  LINK_PATTERN         = r'"clipUrl":"(.*?)"'
  NAME_PATTERN         = r'"clipTitle":"(?P<N>.*?)"'
  API_URL              = 'www.ardmediathek.de/play/config/'

	def handle_free(self, pyfile):
		m = re.search(self.DOC_ID_PATTERN, self.data)

		if not m:
    	self.fail(_('Could not find necessary Document ID'))

    doc_id = m.group(1)
    self.log_debug('found document ID %s' % doc_id)

    self.data = self.load(self.API_URL + doc_id, get={'displaytype':'pc'})
    self.grab_info()
    super(ARD, self).handle_free(pyfile)
