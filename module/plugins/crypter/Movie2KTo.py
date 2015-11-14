# -*- coding: utf-8 -*-

import re
from collections import defaultdict
from module.plugins.internal.Crypter import Crypter

from tempfile import NamedTemporaryFile

class Movie2kTo(Crypter):
    __name__ = 'Movie2kTo'
    __type__ = 'container'
    __pattern__ = r'http://(?:www\.)?movie4k(?:proxy)?\.(?:to|com)/+(.*)'
    __version__ = '0.6'
    __config__ = [('hoster_blacklist', 'str', 'List of non-accepted hosters (space separated)', ''),
                  ('dir_quality', 'bool', 'Show the quality of the footage in the folder name', 'True'),
                  ('whole_season', 'bool', 'Always get the whole season instead of just one episode', 'True'),
                  ('firstN', 'int', 'Get the first N links for each file and hoster', '3')]
    __description__ = """Movie4k.to Container Plugin"""
    __author_name__ = ('4Christopher, igel')
    __author_mail__ = ('4Christopher@gmx.de, ')
    BASE_URL_PATTERN = r'http://(?:www\.)?movie4k\.to/+'
    EPISODE_URL_PATH_PATTERN = r'(?P<name>.+)-(?:online-serie|watch-tvshow)-(?P<id>\d+)'
    FILM_URL_PATH_PATTERN = r'(?P<name>.+)-(?:online-film|watch-movie)-(?P<id>\d+)'
    TVSHOW_URL_PATH_PATTERN = r'tvshows-(?P<mode>[^-]*)-(?P<season>\d*)-?(?P<name>.+)'
    SEASON_PATTERN = r'<TD id="tdmovies" width="[^"]*"><a href="([^"]*)">.*?Season:\s*(\d*)'
    SEASON_DROPDOWN_PATTERN = r'<SELECT name="season".*?value="([^"]*)" selected'
    # detect links in the javascript or html code
    DETECT_JS_LINK_PATTERN = r'links\[(\d+?)\].+?([\w\s.]+?)</a></td>(.+?)</tr>'
    DETECT_HTML_LINK_PATTERN = r'<tr id="tablemoviesindex2".+?<a href=".+?(\d{4,7}).*?">.+?([\w\s.]+)</a></td>(.+?)</tr>'
    # combine the pregrep pattern with the season number to get the correct season's episodes
    EPISODE_DROPDOWN_PREGREP_PATTERN = '<FORM name="episodeform%s">.*?</FORM>'
    EPISODE_DROPDOWN_PATTERN = r'<OPTION value="([^"]*)".*?>Episode\s*(\d*) '
    EPISODE_PATTERN = r'<TD id="tdmovies" width="[^"]*"><a href="([^"]*)">.*?Episode:\s*(\d*)'
    BASE_URL = 'http://www.movie4k.to'

    def getInfo(self, url_path):
        self.format = 'other'
        # 3 possibilities: 1. a movie, 2. a TV-show episode, 3. something else (entire show or season)
        pattern_re = re.search(self.FILM_URL_PATH_PATTERN, url_path)
        if pattern_re is not None:
            self.format = 'movie'
        else:
            pattern_re = re.search(self.EPISODE_URL_PATH_PATTERN, url_path)
            if pattern_re is not None:
                self.format = 'episode'
        # if we have detected a movie or a TV show episode, then we have a name and an id
        if self.format != 'other':
            self.name = pattern_re.group('name')
            self.id = pattern_re.group('id')
            self.log_debug('URL Path: %s (ID: %s, Name: %s, Format: %s)'
                      % (url_path, self.id, self.name, self.format))

    def handle_show(self, url_path, name):
        # load the webpage
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))
        # get all seasons for this show
        seasons = re.findall(self.SEASON_PATTERN, self.html)
        # handle each season individually
        for sURL, sNR in seasons:
            handle_season(sURL, name, sNR)



    def handle_season(self, url_path, name, sNR):
        # set the season as subfolder of the name
        folder = '%s/Season %s' % (name, self.tvshow_number(sNR))

        # load the webpage
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))
        # add the links of the episodes to the collected links for this season
        regex = re.compile(self.EPISODE_PATTERN)

        season_links = []
        for match in regex.finditer(self.html):
            season_links += self.get_episode_links(match.group(1))            
        # add Quality suffix if configured
        augmented_name = "%s%s" % (name, self.qStat())
        self.packages.append((augmented_name, season_links, folder))


    def handle_season_from_episode(self, url_path):
        # load the webpage
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))

        # get the season number
        m = re.search(self.SEASON_DROPDOWN_PATTERN, self.html, re.MULTILINE | re.DOTALL)
        if not m:
          self.parseError("could not parse %s/%s, please check spelling" % (self.BASE_URL, url_path))

        sNR = m.group(1)

        # set the season as subfolder of the name
        folder = '%s/Season %s' % (self.name, self.tvshow_number(sNR))

        # find the selected episode list
        pregrep_pattern = self.EPISODE_DROPDOWN_PREGREP_PATTERN % sNR
        self.log_debug('finding dropdown pregrep pattern: %s' % pregrep_pattern)
        selected_episodes = re.search(pregrep_pattern, self.html, re.MULTILINE | re.DOTALL)

        self.log_debug('finding %s in %s' % (self.EPISODE_DROPDOWN_PATTERN, selected_episodes.group(0)))

        # add the links of the episodes to the collected links for this season
        regex = re.compile(self.EPISODE_DROPDOWN_PATTERN)

        season_links = []
        for match in regex.finditer(selected_episodes.group(0)):
            season_links += self.get_episode_links(match.group(1))            
        # add Quality suffix if configured
        augmented_name = "%s%s" % (self.name, self.qStat())
        self.packages.append((augmented_name, season_links, folder))




    # handle entire TV show or entire season
    def handle_other(self, url_path):
        # 2 possibilities: an entire TV show or a TV-show season
        pattern_re = re.search(self.TVSHOW_URL_PATH_PATTERN, url_path)
        if pattern_re is not None:
            if pattern_re.group('mode') == 'season':
                # an entire TV show: recursive call for all its seasons
                name = pattern_re.group('name')
                self.log_debug('handling TV show ' + name)
                self.handle_show(url_path, name)
            elif pattern_re.group('mode') == 'episode':
                # a season: get all its episodes
                name = pattern_re.group('name')
                seasonNR = pattern_re.group('season')
                self.log_debug('handling season ' + seasonNR + ' of ' + name)
                self.handle_season(url_path, name, seasonNR)
            else:
                self.fail('could not detect download type of ' + url_path)
        else:
            self.fail('could not detect download type of '+ url_path)
        
    def decrypt(self, pyfile):
        self.package = pyfile.package()
        self.qStatReset()
        url_path = re.match(self.__pattern__, pyfile.url).group(1)
        self.getInfo(url_path)

        if (self.format == 'movie') or (self.format == 'episode'):
            if(self.get_config('whole_season') and (self.format == 'episode')):
              self.handle_season_from_episode(url_path)
            else:
              links = self.getLinks(url_path)
              name = '%s%s' % (self.package.name, self.qStat())
              self.packages.append((name, links, self.package.folder))            
        else:
            self.handle_other(url_path)

    def get_episode_links(self, url_path):
        self.getInfo(url_path)
        return self.getLinks(url_path)

    ## This function returns the links for one episode/movie as list
    def getLinks(self, url_path):
        # read config
        hoster_blacklist = re.findall(r'\b(\w+?)\b', self.get_config('hoster_blacklist'))
        firstN = self.get_config('firstN')
        links = []
        # prepare patterns:
        # The quality is one digit. 0 is the worst and 5 is the best. It's not always there.
        re_quality = re.compile(r'.+?Quality:.+?smileys/(\d)\.gif')
        # the hoster IDs can be parsed from the javascript "links"-array
        re_hoster_id_js = re.compile(self.DETECT_JS_LINK_PATTERN)
        # I assume that the ID is 7 digits
        re_hoster_id_html = re.compile(self.DETECT_HTML_LINK_PATTERN)
        
        # load the page        
        self.html = self.load("%s/%s" % (self.BASE_URL, url_path))
        # parse for IDs
        matches = re_hoster_id_js.findall(self.html) + re_hoster_id_html.findall(self.html)

        self.log_debug('found the following %d matches in %s/%s:' % (len(matches), self.BASE_URL, url_path))
        self.log_debug(matches)

        if len(matches) == 0:
            self.fail('no links')
        
        count = defaultdict(int)
        ## h_id: hoster_id of a possible hoster
        for h_id, hoster, q_html in matches:
            if hoster not in hoster_blacklist:
                self.log_debug('Accepted: %s, ID: %s' % (hoster, h_id))
                match_q = re_quality.search(q_html)
                if match_q:
                    # if the quality indicator is not omitted, note the quality of this movie
                    quality = int(match_q.group(1))
                    if self.max_q == None:
                        self.max_q = quality
                    else:
                        if self.max_q < quality:
                            self.max_q = quality
                    self.log_debug('Quality: %d' % quality)
            
                count[hoster] += 1
                if count[hoster] <= firstN:
                    if match_q: self.q.append(quality)
                    if h_id != self.id:
                        if self.format != 'movie':
                            self.log_debug('detected TV show episode, loading %s/tvshows-%s-%s.html' % (self.BASE_URL, h_id, self.name))
                            self.html = self.load('%s/tvshows-%s-%s.html' % (self.BASE_URL, h_id, self.name))
                        else:
                            self.log_debug('detected movie, loading %s/%s-watch-movie-%s.html' % (self.BASE_URL, self.name, h_id))
                            self.html = self.load('%s/%s-watch-movie-%s.html' % (self.BASE_URL, self.name, h_id))
                            
                    else:
                        self.log_debug('This is already the right ID')
                    # The iframe tag must continue with a width. There where
                    # two iframes in the site and I try to make sure that it
                    # matches the right one. This is not (yet) nessesary
                    # because the right iframe happens to be the first iframe.
                    for pattern in (r'<a target="_blank" href="(http://[^"]*?)"',
                                    r'<iframe src="(http://[^"]*?)" width'):
                        try:
                            url = re.search(pattern, self.html).group(1)
                        except:
                            self.log_debug('Failed to find the URL (pattern %s)' % pattern)
                        else:
                            self.log_debug('id: %s, %s: %s' % (h_id, hoster, url))
                            links.append(url)
                            break
            else:
                self.log_debug('Not accepted since %s is blacklisted' % hoster)
        # self.log_debug(links)
        return links


    def qStat(self):
        if len(self.q) == 0:
            return ''
        if not self.get_config('dir_quality'):
            return ''
        if len(self.q) == 1:
            return ' (Quality: %d)' % self.q[0]
        return ' (Average quality: %d, min: %d, max: %d)' % ((sum(self.q) / float(len(self.q))), min(self.q), max(self.q))


    def qStatReset(self):
        self.q = [] # to calculate the average, min and max of the quality
        self.max_q = None # maximum quality of all hosters


    def tvshow_number(self, number):
        if int(number) < 10:
            return '0%s' % number
        else:
            return number


    def name_tvshow(self, season, ep):
        return '%s S%sE%s' % (self.name, self.tvshow_number(season), self.tvshow_number(ep))
