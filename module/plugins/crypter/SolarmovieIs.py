# -*- coding: utf-8 -*-

import re
import pycurl
from collections import defaultdict
from module.plugins.internal.Crypter import Crypter

class SolarmovieIs(Crypter):
    __name__ = 'SolarmovieIs'
    __type__ = 'container'
    __pattern__ = r'http://(?:www\.)?solarmovie\.is/+(.*)'
    __version__ = '0.1'
    __config__ = [('hoster_blacklist', 'str', 'List of non-accepted hosters (space separated)', '')]
    __description__ = """Solarmovie.is Container Plugin"""
    __author_name__ = ('igel')
    __author_mail__ = ('')

    BASE_URL = 'http://www.solarmovie.is'
    CINE_BASE_URL = 'http://cinema.solarmovie.is'
    PLAY_BASE = '/link/play/'
    TV_URL_PATH_PATTERN = r'tv/(?P<name>.*?)-(?P<year>\d+)(?P<remain>/.*)'
    TV_SEASON_URL_PATH_PATTERN = r'season-(?P<snr>\d+)(?P<remain>/.*)'
    TV_EPISODE_URL_PATH_PATTERN = r'episode-(?P<enr>\d+)'

    # find seasons in a TV show page
    SEASON_PATTERN = '<a href="(?P<sURL>/tv/.+?)">(?:.|\n)+?Season (?P<sNR>\d+)\s*</a>'

    # find the name of the TV show
    NAME_PATTERN = '\s*(?P<name>.+?)(?:\s|\n)*<a class="year" href=".*?">'

    # find the name (and season number) of the TV show on a season-page
    SEASON_INFO_PATTERN = r'<a href="/tv/.*?">(?P<name>.*?)</a> <span class="season_episode">/ Season (?P<sNR>\d+)</span>'

    # find episodes on a season-page
    EPISODE_PATTERN = '<a href="(?P<eURL>/tv/.+?)" class="linkCount typicalGrey">(?:\s|\n)*?\d+ links</a>'

    # find a link on an episode/movie-page
    ID_PATTERN = '<tr id="link_(?P<ID>\d+)".*?<a href="/link/show/(?P<ID2>\d+)/">(?:\s|\n)*(?P<hoster>\w+\.\w+)\s*</a>'

    # find the iframe in the play-movie page
    HOSTER_FRAME_PATTERN = r'<iframe.*?src="(.*?)"'

    # find info about the episode in the episode page
    EPISODE_INFO_PATTERN = '<span class="season_episode">/ Episode (?P<eNR>\d+)</span>(?:.|\n)*?<div class="breadcrumb">(?:\s|\n)*<ul>(?:\s|\n)*<li><a href="/tv/.+?">(?P<sName>.+?)</a></li>(?:\s|\n)*<li><a href="/tv/.+?">\s*Season (?P<sNR>\d+)\s*</a></li>'

    # this is much too slow, dunno why...
    #EPISODE_INFO_PATTERN = r'\s*(?P<eName>.+?)(?:\s|\n)*<span class="season_episode">/ Episode (?P<eNR>\d+)</span>(?:.|\n)*?<div class="breadcrumb">(?:\s|\n)*<ul>(?:\s|\n)*<li><a href="/tv/.+?">(?P<sName>.+?</a></li>(?:\s|\n)*<li><a href="/tv/.+?">\s*Season (P:<sNR>\d+)\s*</a></li>'
    

    # find info about the movie in the movie page
    MOVIE_INFO_PATTERN = r'\s*(?P<name>.+?)(?:\s|\n)*<a class="year" href=".*?">(?:\s|\n)*(?P<year>\d+)</a>'

    def getInfo(self, url_path):
        # it's either a movie or some TV show/season/episode
        pattern_re = re.search(self.TV_URL_PATH_PATTERN, url_path)
        if pattern_re is None:
            self.format = 'movie'
        else:
            url_extension = pattern_re.group('remain')
            pattern_re = re.search(self.TV_SEASON_URL_PATH_PATTERN, url_extension)
            if pattern_re is None:
                self.format = 'show'
            else:
                url_extension = pattern_re.group('remain')
                pattern_re = re.search(self.TV_EPISODE_URL_PATH_PATTERN, url_extension)
                if pattern_re is None:
                    self.format = 'season'
                else:
                    self.format = 'episode'

    # turn "embedded"-link into normal link
    def unembed(self, link):
        return re.sub(r'embed-(.*?)-.*', r'\1', link)

    # extract links from self.html
    def getLinks(self):
        # read config
        hoster_blacklist = re.findall(r'\b(\w+?)\b', self.getConfig('hoster_blacklist'))
        
        # get the links
        ids = re.findall(self.ID_PATTERN, self.html, re.MULTILINE | re.DOTALL)
        links = []
        for current_id, current_id2, hoster in ids:
            if hoster not in hoster_blacklist:
                self.logDebug('getting link at %s (id %s)' % (hoster, current_id))
                links.append(self.getLink(current_id))
        return links

    def getLink(self, my_id):
        # clear cookies
        self.req.http.c.setopt(pycurl.COOKIELIST, "ALL");
        # solarmovies sometimes doesn't like gzip/deflate encoding and sends us into an infinite redirect, so clear the encoding flag
        self.req.http.c.setopt(pycurl.ENCODING, "");
        # load the page        
        self.html = self.load("%s%s%s/" % (self.CINE_BASE_URL, self.PLAY_BASE, my_id), cookies=False)

        # get the frame source
        link = re.search(self.HOSTER_FRAME_PATTERN, self.html, re.IGNORECASE | re.MULTILINE | re.DOTALL).group(1)
        self.logDebug('found link %s' % link)
        # get the non-embedded vesion
        return self.unembed(link)
 

    def handle_show(self, url_path):
        # load the webpage
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))
        # get the name of the show
        self.name = re.find(self.NAME_PATTERN, self.html, re.MULTILINE).group('name')
        # get all seasons for this show
        seasons = re.findall(self.SEASON_PATTERN, self.html, re.MULTILINE)
        # handle each season individually
        for sURL, sNR in seasons:
            handle_season(sURL)


    def handle_season(self, url_path):
        # load the webpage
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))
        # get the name of the TV show
        season_info = re.find(self.SEASON_INFO_PATTERN, self.html)
        if not hasattr(self, 'name') or self.name is None:
          self.name = season_info.group('name')
        self.sNR = int(season_info.group('sNR'))

        # set the season as subfolder of the name
        self.folder = '%s - Season %s' % (self.name, self.sNR)

        # add the links of the episodes to the collected links for this season
        episodes = re.findall(self.EPISODE_PATTERN, self.html, re.MULTILINE)
        season_links = []
        for eURL in episodes:
            # load the page
            self.html = self.load("%s/%s" % (self.BASE_URL, eURL))
            # parse the links
            season_links += self.getLinks()
        # add the package
        self.packages.append((self.folder, season_links, self.folder))


    def handle_episode(self, url_path):
        # load the page
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))
        # get the episode info
        einfo = re.search(self.EPISODE_INFO_PATTERN, self.html, re.MULTILINE)
        if not hasattr(self, 'name') or self.name is None:
            self.name = einfo.group('sName')
        if not hasattr(self, 'sNR') or self.sNR is None:
            self.sNR = einfo.group('sNR')
        # set the season as subfolder of the name
        if not hasattr(self, 'folder') or self.folder is None:
          self.folder = '%s - Season %s' % (self.name, self.sNR)
        # get the links
        links = self.getLinks()
        # add the package
        self.packages.append((self.folder, links, self.folder))


    def handle_movie(self, url_path):
        # load the page
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))
        # get the movie info
        minfo = re.search(self.MOVIE_INFO_PATTERN, self.html, re.MULTILINE)
        # set the season as subfolder of the name
        self.folder = '%s [%s]' % (minfo.group('name'), minfo.group('year'))
        # get the links
        links = self.getLinks()
        # add the package
        self.packages.append((self.folder, links, self.folder))


    # dictionary deciding which function to call for each format
    handlers = {'show': handle_show,
               'season': handle_season,
               'episode': handle_episode,
               'movie': handle_movie
              }
  
    def decrypt(self, pyfile):
        self.package = pyfile.package()
        url_path = re.match(self.__pattern__, pyfile.url).group(1)
        self.getInfo(url_path)
        self.logDebug('detected format: %s' % self.format)
        self.handlers[self.format](self,url_path)


