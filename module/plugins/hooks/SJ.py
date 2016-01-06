from module.plugins.internal.Addon import Addon
import feedparser, re, urllib, urllib2, httplib, codecs, base64
from module.network.RequestFactory import getURL 
from BeautifulSoup import BeautifulSoup
import smtplib
import pycurl

try:
    import simplejson as json
except ImportError:
    import json

def getSeriesList(file):
    try:
        titles = []
        f = codecs.open(file, "rb", "utf-8")
        for title in f.read().splitlines():
            if len(title) == 0:
                continue
            title = title.replace(" ", ".")
            titles.append(title)
        f.close()
        return titles
    except UnicodeError:
        self.core.log.error("Abbruch, es befinden sich ungueltige Zeichen in der Suchdatei!")
    except IOError:
        self.core.log.error("Abbruch, Suchdatei wurde nicht gefunden!")
    except Exception, e:
        self.core.log.error("Unbekannter Fehler: %s" %e)

def send_mail(text):
    """Tested with googlemail.com and bitmessage.ch. It should work with all mailservices which provide SSL access.""" 
    serveraddr = ''
    serverport = '465'
    username = ''
    password = ''
    fromaddr = ''
    toaddrs  = ''
    
    if toaddrs == "":
        return

    subject = "pyLoad: Package added!"
    msg = "\n".join(text)

    header = "To: %s\nFrom:%s\nSubject:%s\n" %(toaddrs,fromaddr,subject)
    msg = header + "\n" + msg

    server = smtplib.SMTP_SSL(serveraddr,serverport)
    server.ehlo()
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
    
def notifyPushover(api ='', api2 ='', msg=''):
    data = urllib.urlencode({
        'user': api,
        'token': api2,
        'title': 'pyLoad: SJHook added Package',
        'message': "\n\n".join(msg)
    })
    try:
        req = urllib2.Request('https://api.pushover.net/1/messages.json', data)
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        print 'Failed much'
        return False
    res = json.load(response)
    if res['status'] == 1:
        print 'Pushover Success'
    else:
        print 'Pushover Fail' 
    
def notifyPushbullet(api='', msg=''):
    data = urllib.urlencode({
        'type': 'note',
        'title': 'pyLoad: SJHook added Package',
        'body': "\n\n".join(msg)
    })
    auth = base64.encodestring('%s:' %api).replace('\n', '')
    try:
        req = urllib2.Request('https://api.pushbullet.com/v2/pushes', data)
        req.add_header('Authorization', 'Basic %s' % auth)
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        print 'Failed much'
        return False
    res = json.load(response)
    if res['sender_name']:
        print 'Pushbullet Success'
    else:
        print 'Pushbullet Fail'

class SJ(Addon):
    __name__ = "SJ"
    __type__    = "hook"
    __version__ = "2.8"
    __status__  = "testing"
    __description__ = "Findet und fuegt neue Episoden von SJ.org pyLoad hinzu"
    __config__ = [("activated", "bool", "Aktiviert", "False"),
                  ("regex","bool","Eintraege aus der Suchdatei als regulaere Ausdruecke behandeln", "False"),
                  ("quality", """480p;720p;1080p""", "480p, 720p oder 1080p", "720p"),
                  ("file", "file", "Datei mit Seriennamen", "SJ.txt"),
                  ("rejectlist", "str", "Titel ablehnen mit (; getrennt)", "dd51;itunes"),
                  ("language", """DEUTSCH;ENGLISCH""", "Sprache", "DEUTSCH"),
                  ("interval", "int", "Interval", "60"),
                  ("hoster", """ul;so;fm;cz;alle""", "ul.to, filemonkey, cloudzer, share-online oder alle", "ul"),
                  ("pushoverapi", "str", "deine pushoverapi user key", ""),
                  ("pushoverapi2", "str", "deine pushoverapi api key", ""),
                  ("queue", "bool", "Direkt in die Warteschlange?", "False"),
                  ("pushbulletapi","str","Your Pushbullet-API key","")]
    __author_name__ = ("gutz-pilz","zapp-brannigan")
    __author_mail__ = ("unwichtig@gmail.com","")

    MIN_CHECK_INTERVAL = 2 * 60 #2minutes

    def activate(self):
        self.periodical.start(self.config.get('interval') * 60)

    def periodical_task(self):
        feed = feedparser.parse('http://serienjunkies.org/xml/feeds/episoden.xml')
        self.pattern = "|".join(getSeriesList(self.config.get("file"))).lower()
        reject = self.config.get("rejectlist").replace(";","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = self.config.get("hoster")
        if self.hoster == "alle":
            self.hoster = "."
        self.added_items = []
        
        for post in feed.entries:
            link = post.link
            title = post.title
            
            if self.config.get("regex"):
                m = re.search(self.pattern,title.lower())
                if not m and not "720p" in title and not "1080p" in title:
                    m = re.search(self.pattern.replace("480p","."),title.lower())
                    self.quality = "480p"
                if m:
                    if "720p" in title.lower(): self.quality = "720p"
                    if "1080p" in title.lower(): self.quality = "1080p"
                    m = re.search(reject,title.lower())
                    if m:
                        self.log_debug("Abgelehnt: " + title)
                        continue
                    title = re.sub('\[.*\] ', '', post.title)
                    self.range_checkr(link,title)
                                
            else:
                if self.config.get("quality") != '480p':
                    m = re.search(self.pattern,title.lower())
                    if m:
                        if self.config.get("language") in title:
                            mm = re.search(self.quality,title.lower())
                            if mm:
                                mmm = re.search(reject,title.lower())
                                if mmm:
                                    self.log_debug("Abgelehnt: " + title)
                                    continue
                                title = re.sub('\[.*\] ', '', post.title)
                                self.range_checkr(link,title)
        
                else:
                    m = re.search(self.pattern,title.lower())
                    if m:
                        if self.config.get("language") in title:
                            if "720p" in title.lower() or "1080p" in title.lower():
                                continue
                            mm = re.search(reject,title.lower())
                            if mm:
                                self.log_debug("Abgelehnt: " + title)
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link,title)

        if len(self.config.get('pushbulletapi')) > 2:
            notifyPushbullet(self.config.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True
        if len(self.config.get('pushoverapi')) > 2:
            notifyPushover(self.config.get("pushoverapi"),self.config.get("pushoverapi2"),self.added_items) if len(self.added_items) > 0 else True
        send_mail(self.added_items) if len(self.added_items) > 0 else True 
                    
    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            for count in range(int(number1),(int(number2)+1)):
                NR = re.match("d\{2}", str(count))
                if NR is not None:
                    title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                    self.range_parse(link, title1)
                else:
                    title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                    self.range_parse(link, title1)
        else:
            self.parse_download(link, title)


    def range_parse(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)
        titles = soup.findAll(text=re.compile(search_title))
        for title in titles:
           if self.quality !='480p' and self.quality in title: 
               self.parse_download(series_url, title)
           if self.quality =='480p' and not (('.720p.' in title) or ('.1080p.' in title)):               
               self.parse_download(series_url, title)


    def parse_download(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)
        title = soup.find(text=re.compile(search_title))
        if title:
            items = []
            links = title.parent.parent.findAll('a')
            for link in links:
                url = link['href']
                pattern = '.*%s_.*' % self.hoster
                if re.match(pattern, url):
                    items.append(url)
            self.send_package(title,items) if len(items) > 0 else True

    def send_package(self, title, link):
        try:
            storage = self.db.retrieve(title)
        except Exception:
            self.log_debug("db.retrieve got exception, title: %s" % title)                 
        if storage == 'downloaded':
            self.log_debug(title + " already downloaded")
        else:
            self.log_info("NEW EPISODE: " + title)
            self.db.store(title, 'downloaded')
            self.pyload.api.addPackage(title.encode("utf-8"), link, 1 if self.config.get("queue") else 0)
            self.added_items.append(title.encode("utf-8"))
