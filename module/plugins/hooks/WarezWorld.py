import httplib
import re
import StringIO
import sys
import traceback
import urllib
import urllib2
from bs4 import BeautifulSoup as Soup
from datetime import datetime
from module.plugins.internal.Addon import Addon
from pytz import timezone


UNIX_EPOCH = timezone('UTC').localize(datetime(1970, 1, 1))


def notifyPushover(**kwargs):
    Data = kwargs
    Connection = httplib.HTTPSConnection('api.pushover.net:443')
    Connection.request('POST', '/1/messages.json', urllib.urlencode(Data),
                       {'Content-type': 'application/x-www-form-urlencoded'})
    Response = Connection.getresponse()

def replaceUmlauts(title):
    title = title.replace(unichr(228), 'ae').replace(unichr(196), 'Ae')
    title = title.replace(unichr(252), 'ue').replace(unichr(220), 'Ue')
    title = title.replace(unichr(246), 'oe').replace(unichr(214), 'Oe')
    title = title.replace(unichr(223), 'ss')
    title = title.replace('&amp;', '&')
    return title

def getUnixTimestamp(String):
    String = re.search(r'^.*(\d{2}.\d{2}.\d{4})(\d{1,2}):(\d{2}).*$', String)
    if String:
        String = String.group(1) + \
            ('0' + String.group(2) if String.group(2) < '10' else String.group(2)) + \
            String.group(3)
        String = String.replace('.', '')

    UnixTimestamp = (
        timezone('Europe/Berlin').localize(datetime.strptime(String, '%d%m%Y%H%M')).astimezone(timezone('UTC'))
            - UNIX_EPOCH
    ).total_seconds()
    return UnixTimestamp


class WarezWorld(Addon):
    __name__ = 'WarezWorld'
    __type__ = 'hook'
    __status__ = 'testing'
    __author_name__ = ('Arno-Nymous')
    __author_mail__ = ('Arno-Nymous@users.noreply.github.com')
    __version__ = '1.2'
    __description__ = 'Get new movies from Warez-World.org'
    __config__ = [
        ('activated', 'bool', 'Active', 'False'),
        ('interval', 'int', 'Waiting time until next run in minutes', '60'),
        ('minYear', 'long', 'No movies older than year', '1970'),
        ('pushoverAppToken', 'str', 'Pushover app token', ''),
        ('pushoverUserToken', 'str', 'Pushover user token', ''),
        ('preferredHosters', 'str', 'Preferred hosters (seperated by;)','Share-online.biz'),
        ('quality', '720p;1080p', 'Video quality', '720p'),
        ('ratingCollector', 'float', 'Send releases to link collector with an IMDb rating of (or higher)', '6.5'),
        ('ratingQueue', 'float', 'Send releases to queue with an IMDb rating of (or higher)', '8.0'),
        ('rejectGenres', 'str', 'Reject movies of an of the following genres (seperated by ;)', 'Anime;Documentary;Family'),
        ('rejectReleaseTokens', 'str', 'Reject releases containing any of the following tokens (seperated by ;)', '.ts.;.hdts.'),
        ('soundError', ';none;alien;bike;bugle;cashregister;classical;climb;cosmic;echo;falling;gamelan;incoming;intermission;magic;mechanical;persistent;pianobar;pushover;siren;spacealarm;tugboat;updown', 'Use this sound for errors pushed via Pushover (empty for default)', ''),
        ('soundNotification', ';none;alien;bike;bugle;cashregister;classical;climb;cosmic;echo;falling;gamelan;incoming;intermission;magic;mechanical;persistent;pianobar;pushover;siren;spacealarm;tugboat;updown', 'Use this sound for notifications pushed via Pushover (empty for default)', '')
    ]

    UrlOpener = urllib2.build_opener()
    RejectGenres = []
    RejectReleaseTokens = []
    LastReleaseTimestamp = None
    # Initialize dictionary keys here to enable quick access on keys via augmented operators
    # in later code without further code magic
    Statistics = {'Total': 0, 'Added': 0, 'Skipped': 0, 'AlreadyProcessed': 0}

    def __init__(self, *args, **kwargs):
        super(WarezWorld, self).__init__(*args, **kwargs)
        self.start_periodical(self.get_config('interval'))

    def periodical(self):
        self.log_info(u'Start periodical run...')

        self.interval = self.get_config('interval') * 60
        self.RejectGenres = self.get_config('rejectGenres').split(';')
        self.PreferredHosters = self.get_config('preferredHosters').lower().split(';')
        self.RejectReleaseTokens = self.get_config('rejectReleaseTokens').lower().split(';')
        self.LastReleaseTimestamp = float(self.retrieve('LastReleaseTimestamp', 0))
        # Setting statistics to 0 by iterating over dictionary items
        # instead of recreating dictionary over and over
        for Key in self.Statistics:
            self.Statistics[Key] = 0

        try:
            Request = urllib2.Request('http://warez-world.org/kategorie/filme', 'html5lib')
            Request.add_header('User-Agent', 'Mozilla/5.0')
            Page = Soup(self.UrlOpener.open(Request).read())
            Items = Page.findAll('li', class_='main-single')
            Releases = []

            for Item in Items:
                Releases.append({
                    'MovieName': Item.find('span', class_='main-rls').text,
                    'ReleaseName': re.search(r'<br/>(.*)</span>', unicode(Item.find('span', class_='main-rls'))).group(1),
                    'ReleaseLink': unicode(Item.find('span', class_='main-rls').a['href']),
                    'ReleaseDate': getUnixTimestamp(unicode(Item.find(class_='main-date').text))
                })
            self.log_info(u'{0} releases found'.format(len(Releases)))

            for Release in Releases[::-1]:
                if (Release['ReleaseDate'] < self.LastReleaseTimestamp):
                    self.log_debug(u'Release already processed \"{0}\"'.format (Release['ReleaseName']))
                    self.Statistics['AlreadyProcessed'] += 1
                    continue
                self.log_debug(u'Processing release \"{0}\"'.format(Release['ReleaseName']))
                Release['MovieYear'] = 1900
                Release['MovieRating'] = 0
                Release['MovieGenres'] = []
                if self.parseRelease(Release):
                    self.downloadRelease(Release)

            self.store('LastReleaseTimestamp', Releases[0]['ReleaseDate'])
            self.log_debug(u'Last parsed release timestamp is {0}'.format(Releases[0]['ReleaseDate']))

            self.Statistics['Total'] = sum(self.Statistics.itervalues())
            self.log_info(u'Periodical run finished. Statistics: {0} total, {1} added, {2} skipped, {3} already processed'.format(
                self.Statistics['Total'],
                self.Statistics['Added'],
                self.Statistics['Skipped'],
                self.Statistics['AlreadyProcessed']
            ))
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            output = StringIO.StringIO()
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=output)
            if 'Release' in locals():
                msg = '<b>Stacktrace</b>\n{0}\n<b>Release</b>\n{1}\n\n<b>Date</b>\n{2}'.format(
                    output.getvalue(), Release['ReleaseName'].encode('utf-8'), Release['ReleaseDate']
                )
            else:
                msg = '<b>Stacktrace</b>\n{0}'.format(output.getvalue())
            notifyPushover(
                token=self.get_config('pushoverAppToken'),
                user=self.get_config('pushoverUserToken'),
                title='Error in script \"WarezWorld.py\"',
                message=msg,
                sound=self.get_config('soundError'),
                html=1
            )
            raise

    def parseRelease(self, Release):
        if any([
            set(re.split(r'[\. ]', Release['ReleaseName'].lower())) & set(self.RejectReleaseTokens),
            not(self.get_config('quality').lower() in Release['ReleaseName'].lower())
        ]):
            self.log_debug(u'...Skip release ({0})'.format("Release name contains unwanted tokens or quality mismatch"))
            self.Statistics['Skipped'] += 1
            return False

        Request = urllib2.Request(Release['ReleaseLink'], 'html5lib')
        Request.add_header('User-Agent', 'Mozilla/5.0')
        ReleasePage = Soup(self.UrlOpener.open(Request).read())

        DownloadLinks = ReleasePage.findAll('div', id='download-links')
        if DownloadLinks:
            for DownloadLink in DownloadLinks:
                if DownloadLink.a.string and DownloadLink.a.string.lower() in self.PreferredHosters:
                    Release['DownloadLink'] = DownloadLink.a['href']
                    break
        if 'DownloadLink' not in Release:
            self.log_debug('...No download link of preferred hoster found')
            return False

        ReleaseNfo = ReleasePage.find('div', class_='spoiler')
        ImdbUrl = re.search(r'(http://)?.*(imdb\.com/title/tt\d+)\D', unicode(ReleaseNfo))
        if ImdbUrl:
            Release['ImdbUrl'] = 'http://www.' + ImdbUrl.group(2)
            self.addImdbData(Release)
        else:
            for Div in ReleasePage.findAll('div', class_='ui2'):
                if Div.a and Div.a.string == 'IMDb-Seite':
                    Request = urllib2.Request(urllib.quote_plus(Div.a['href'].encode('utf-8'), '/:?='))
                    ImdbPage = Soup(self.UrlOpener.open(Request).read())
                    if ImdbPage.find('table', class_='findList'):
                        Release['ImdbUrl'] = 'http://www.imdb.com' + \
                            ImdbPage.find('td', class_='result_text').a['href']
                        self.addImdbData(Release)
                    else:
                        self.log_debug(u'...Could not obtain IMDb data for release...Send to link collector')
                        self.Statistics['Added'] += 1
                    break

        if all([Release['MovieYear'] >= self.get_config('minYear'),
                Release['MovieRating'] >= self.get_config('ratingCollector'),
                not(set(Release['MovieGenres']) & set(self.RejectGenres))]):
            return True
        else:
            self.log_debug(u'...Skip release ({0})'.format('Movie too old, poor IMDb rating or unwanted genres'))
            self.Statistics['Skipped'] += 1
            return False

    def addImdbData(self, Release):
        self.log_debug(u'...Fetching IMDb data for release ({0})'.format(Release['ImdbUrl']))

        Request = urllib2.Request(Release['ImdbUrl'])
        Request.add_header('User-Agent', 'Mozilla/5.0')
        ImdbPage = Soup(self.UrlOpener.open(Request).read())

        MovieName = ImdbPage.find('span', {'itemprop': 'name'}).string
        # For the year it has to be done a tiny bit of BeautifulSoup magic as it sometimes can
        # be formatted as a link on IMDb and sometimes not
        try:
            MovieYear = ImdbPage.find('h1', class_='header').find('span', class_='nobr').find(
                text=re.compile(r'\d{4}')
            ).strip(u' ()\u2013')
        except:
            MovieYear = 0
            self.log_debug('...Could not parse movie year ({0})'.format(Release['ImdbUrl']))
        try:
            MovieRating = ImdbPage.find('span', {'itemprop': 'ratingValue'}).string.replace(',', '.')
        except:
            MovieRating = 0
            self.log_debug(u'...Could not parse movie rating ({0})'.format(MovieName, Release['ImdbUrl']))
        MovieGenres = []
        try:
            for Genre in ImdbPage.find('div', {'itemprop': 'genre'}).findAll('a'):
                MovieGenres.append(Genre.string.strip())
        except:
            self.log_debug(u'...Could not parse movie genres ({0})'.format(Release['ImdbUrl']))

        Release['MovieName'] = MovieName
        Release['MovieYear'] = MovieYear
        Release['MovieRating'] = MovieRating
        Release['MovieGenres'] = MovieGenres

    def downloadRelease(self, Release):
        Storage = self.retrieve(u'{0} ({1})'.format(Release['MovieName'], Release['MovieYear']))

        if Storage == '1':
            self.log_debug(u'Skip release ({0})'.format('already downloaded'))
            self.Statistics['Skipped'] += 1
        else:
            Storage = u'{0} ({1})'.format(Release['MovieName'], Release['MovieYear'])
            if Release['MovieRating'] >= self.get_config('ratingQueue'):
                self.pyload.api.addPackage(Storage + ' IMDb: ' + Release['MovieRating'],
                                         [Release['DownloadLink']], 1)
                PushoverTitle = 'New movie added to queue'
                self.log_info(u'New movie added to queue ({0})'.format(Storage))
            else:
                self.pyload.api.addPackage(Storage + ' IMDb: ' + Release['MovieRating'],
                                         [Release['DownloadLink']], 0)
                PushoverTitle = 'New movie added to link collector'
                self.log_info(u'New movie added to link collector ({0})'.format(Storage))

            self.Statistics['Added'] += 1

            notifyPushover(
                token=self.get_config('pushoverAppToken'),
                user=self.get_config('pushoverUserToken'),
                title=PushoverTitle,
                message='<b>{0} ({1})</b>\n<i>Rating:</i> {2}\n<i>Genres:</i> {3}\n\n<i>{4}</i>'.format(
                    Release['MovieName'].encode('utf-8'),
                    Release['MovieYear'].encode('utf-8'),
                    Release['MovieRating'].encode('utf-8'),
                    ', '.join(Release['MovieGenres']).encode('utf-8'),
                    Release['ReleaseName'].encode('utf-8')
                ),
                sound=self.get_config('soundNotification'),
                url=(Release['ImdbUrl'].encode('utf-8') if 'ImdbUrl' in Release else ''),
                url_title='View on IMDb',
                html=1
            )

            self.store(Storage, '1')
