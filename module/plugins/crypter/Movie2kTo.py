#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from collections import defaultdict

class Movie2kTo(Crypter):
	__name__ = 'Movie2kTo'
	__type__ = 'container'
	__pattern__ = r'http://(?:www\.)?movie2k\.to/(.*)\.html'
	__version__ = '0.4'
	__config__ = [('accepted_hosters', 'str', 'List of accepted hosters', 'Xvidstage, '),
				('dir_quality', 'bool', 'Show the quality of the footage in the folder name', 'True'),
				('whole_season', 'bool', 'Download whole season', 'False'),
				('everything', 'bool', 'Download everything', 'False'),
				('firstN', 'int', 'Download the first N files for each episode (the first file is probably all you will need)', '1')]
	__description__ = """Movie2k.to Container Plugin"""
	__author_name__ = ('4Christopher')
	__author_mail__ = ('4Christopher@gmx.de')
	BASE_URL_PATTERN = r'http://(?:www\.)?movie2k\.to/'
	TVSHOW_URL_PATH_PATTERN = r'tvshows-(?P<id>\d+?)-(?P<name>.+)'
	FILM_URL_PATH_PATTERN = r'(?P<name>.+?)-(?:online-film|watch-movie)-(?P<id>\d+)'
	SEASON_PATTERN = r'<div id="episodediv(\d+?)" style="display:(inline|none)">(.*?)</div>'
	EP_PATTERN = r'<option value="(.+?)"( selected)?>Episode\s*?(\d+?)</option>'
	BASE_URL = 'http://www.movie2k.to'

	def decrypt(self, pyfile):
		self.package = pyfile.package()
		self.folder = self.package.folder
		self.qStatReset()
		whole_season = self.getConfig('whole_season')
		everything = self.getConfig('everything')
		self.getInfo(pyfile.url)

		if (whole_season or everything) and self.format == 'tvshow':
			self.logDebug('Downloading the whole season')
			for season, season_sel, html in re.findall(self.SEASON_PATTERN, self.html, re.DOTALL | re.I):
				if (season_sel == 'inline') or everything:
					season_links = []
					for url_path, ep_sel, ep in re.findall(self.EP_PATTERN, html, re.I):
						season_name = self.name_tvshow(season, ep)
						self.logDebug('%s: %s' % (season_name, url_path))
						if ep_sel and (season_sel == 'inline'):
							self.logDebug('%s selected (in the start URL: %s)' % (season_name, pyfile.url))
							season_links += self.getInfoAndLinks('%s/%s' % (self.BASE_URL, url_path))
						elif (whole_season and (season_sel == 'inline')) or everything:
							season_links += self.getInfoAndLinks('%s/%s' % (self.BASE_URL, url_path))

					self.logDebug(season_links)
					folder = '%s: Season %s' % (self.name, season)
					name = '%s%s' % (folder, self.qStat())
					self.packages.append((name, season_links, folder))
					self.qStatReset()
		else:
			links = self.getLinks()
			name = '%s%s' % (self.package.name, self.qStat())
			self.packages.append((name, links , self.package.folder))

	def qStat(self):
		if len(self.q) == 0: return ''
		if not self.getConfig('dir_quality'): return ''
		if len(self.q) == 1: return (' (Quality: %d, max (all hosters): %d)' % (self.q[0], self.max_q))
		return (' (Average quality: %d, min: %d, max: %d, %s, max (all hosters): %d)'
			% (sum(self.q) / float(len(self.q)), min(self.q), max(self.q), self.q, self.max_q))
	def qStatReset(self):
		self.q = [] ## to calculate the average, min and max of the quality
		self.max_q = None
	def tvshow_number(self, number):
		if int(number) < 10:
			return '0%s' % number
		else:
			return number

	def name_tvshow(self, season, ep):
		return '%s S%sE%s' % (self.name, self.tvshow_number(season), self.tvshow_number(ep))

	def getInfo(self, url):
		self.html = self.load(url)
		self.url_path = re.match(self.__pattern__, url).group(1)
		self.format = pattern_re = None
		if re.match(r'tvshows', self.url_path):
			self.format = 'tvshow'
			pattern_re = re.search(self.TVSHOW_URL_PATH_PATTERN, self.url_path)
		elif re.search(self.FILM_URL_PATH_PATTERN, self.url_path):
			self.format = 'film'
			pattern_re = re.search(self.FILM_URL_PATH_PATTERN, self.url_path)


		self.name = pattern_re.group('name')
		self.id = pattern_re.group('id')
		self.logDebug('URL Path: %s (ID: %s, Name: %s, Format: %s)'
			% (self.url_path, self.id, self.name, self.format))

	def getInfoAndLinks(self, url):
		self.getInfo(url)
		return self.getLinks()

	## This function returns the links for one episode as list
	def getLinks(self):
		accepted_hosters = re.findall(r'\b(\w+?)\b', self.getConfig('accepted_hosters'))
		firstN = self.getConfig('firstN')
		links = []
		re_quality = re.compile(r'.+?Quality:.+?smileys/(\d)\.gif')
		## The quality is one digit. 0 is the worst and 5 is the best.
		## Is not always there …
		re_hoster_id_html = re.compile(r'(?:<td height|<tr id).+?<a href=".*?(\d{7}).*?".+?&nbsp;([^<>]+?)</a>(.+?)</tr>')
		re_hoster_id_js = re.compile(r'links\[(\d+?)\].+&nbsp;(.+?)</a>(.+?)</tr>')
		## I assume that the ID is 7 digits longs
		count = defaultdict(int)
		matches = re_hoster_id_html.findall(self.html)
		matches += re_hoster_id_js.findall(self.html)
		# self.logDebug(matches)
		## h_id: hoster_id of a possible hoster
		for h_id, hoster, q_html in matches:
			match_q = re_quality.search(q_html)
			if match_q:
				quality = int(match_q.group(1))
				if self.max_q:
					if self.max_q < quality: self.max_q = quality
				else: ## was None before
					self.max_q = quality
				q_s = ', Quality: %d' % quality
			else:
				q_s = ', unknown quality'
			if hoster in accepted_hosters:
				self.logDebug('Accepted: %s, ID: %s%s' % (hoster, h_id, q_s))
				count[hoster] += 1
				if count[hoster] <= firstN:
					if match_q: self.q.append(quality)
					if h_id != self.id:
						self.html = self.load('%s/tvshows-%s-%s.html' % (self.BASE_URL, h_id, self.name))
					else:
						self.logDebug('This is already the right ID')
					try:
						url = re.search(r'<a target="_blank" href="(http://[^"]*?)"', self.html).group(1)
						self.logDebug('id: %s, %s: %s' % (h_id, hoster, url))
						links.append(url)
					except:
						self.logDebug('Failed to find the URL')
			else:
				self.logDebug('Not accepted: %s, ID: %s%s' % (hoster, h_id, q_s))

		# self.logDebug(links)
		return links
