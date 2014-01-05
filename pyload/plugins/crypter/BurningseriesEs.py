# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify #
# it under the terms of the GNU Affero General Public License as #
# published by the Free Software Foundation, either version 3 of the #
# License, or (at your option) any later version. #
# #
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the #
# GNU Affero General Public License for more details. #
# #
# You should have received a copy of the GNU Affero General Public License #
# along with this program. If not, see <http://www.gnu.org/licenses/>. #
############################################################################

################# To do ####################################################
# preferred hoster
# improve packagename
# code cosmetics
############################################################################

import re
from time import sleep
from module.plugins.Crypter import Crypter

class BurningseriesEs(Crypter):
	__name__ = "BurningseriesEs"
	__type__ = "container"
	__pattern__ = r"https://www.burning-seri.es"
	__version__ = "0.01"
	__description__ = """burning-seri.es Overview Plugin"""
	__author_name__ = ("skydevment")
	__author_mail__ = ("development@sky-lab.de")	
	
	BASE_URL = "https://www.burning-seri.es/"
	LINK_PATTERN_DOWNLOADSITE = r'(serie/[-\w]+/\d/.*/Streamcloud-1)'
	LINK_PATTERN_HOSTER = r'(http://streamcloud.eu/\w+/\w+(.*)\.html)'
	TITLE_PATTERN = r'(<h2>(.*)<small>)'
	SEASON_PATTERN = r'(\w+\s\d\s+)'
	
	def setup(self):
		self.multiDL = True
	
	def decrypt(self,pyfile):
		self.process(self.pyfile.url)
	
		
	def process(self, url):
		html = self.load(url)

		new_links = []
		new_package = []

		new_package_name = re.search(self.TITLE_PATTERN,html,re.M).group(2)+ "-" + re.search(self.SEASON_PATTERN,html).group(1).replace(" ","-",1)
		new_package_name = re.sub('\s*','',new_package_name);		

		found = re.findall(self.LINK_PATTERN_DOWNLOADSITE,html)
		if found is None: self.fail("Parser error")
		new_links = found
		for link in new_links:
			new_package.append(self.getDownloadLink(link))
			
		self.packages.append((new_package_name,new_package,new_package_name))
		
	def getDownloadLink(self, url):
		content = self.load(self.BASE_URL+url)
		result = re.search(self.LINK_PATTERN_HOSTER, content)
		return result.group(0)

		
		
	