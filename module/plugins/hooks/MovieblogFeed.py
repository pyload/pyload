# -*- coding: utf-8 -*-
import feedparser
import re
import codecs
import smtplib
import pycurl
import time
from module.plugins.internal.Addon import Addon

def notify(text):
    """Tested with googlemail.com and bitmessage.ch. It should work with all mailservices which provide SSL access.""" 
    serveraddr = ''
    serverport = '465'
    username = ''
    password = ''
    fromaddr = ''
    toaddrs  = ''
    
    if toaddrs == '':
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
    
def notifyPushbullet(apikey,text):
    if apikey == "0" or apikey == "":
        return
    postData = '{"type":"note", "title":"pyLoad: Package added!", "body":"%s"}' %" ### ".join(text).encode("utf-8")
    c = pycurl.Curl()
    c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
    c.setopt(pycurl.URL, 'https://api.pushbullet.com/v2/pushes')
    c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
    c.setopt(pycurl.USERPWD, apikey.encode('utf-8'))
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.POSTFIELDS, postData)
    c.perform()

class MovieblogFeed(Addon):
    __name__ = "MovieblogFeed"
    __type__ = "hook"
    __version__ = "0.13"
    __description__ = "movie-blog.org feed fetcher"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("interval", "int", "Execution interval in minutes", "20"),
                  ("patternfile", "str", "File to search for tv-shows, movies...", "input.txt"),
                  ("destination", "queue;collector", "Link destination", "collector"),
                  ("ignore","str","Ignore pattern (comma seperated)","itunes,chinacam"),
                  ("historical","bool","Use the movie-blog.org search in order to match older entries","False"),
                  ("pushbulletapi","str","Your Pushbullet-API key","0"),
                  ("quiethours","str","Quite hours (comma seperated)","")]
    __authors__ = [("zapp-brannigan", ""), ("pyrexy", "")]
   
    FEED_URL = "http://www.movie-blog.org/feed/"
    SUBSTITUTE = "[&#\s/]"
    
    def activate(self):
        self.start_periodical(self.get_config('interval') * 60)
        
    def readInput(self):
        try:
            f = codecs.open(self.get_config("patternfile"), "rb")
            return f.read().splitlines()
        except:
            self.log_error("Inputfile not found")
            
    def getPatterns(self):
        out = {}
        for line in self.mypatterns:
            if len(line) == 0 or line.startswith("#"):
                continue
            try:
                n = line.split(",")[0]
                q = line.split(",")[1]
                r = line.split(",")[2]
            except:
                self.log_error("Syntax error in [%s] detected, please take corrective action" %self.get_config("patternfile"))
            
            try:
                d = line.split(",")[3]
            except:
                d = ""
            
            if q == "":
                q = r'.*'
                
            if r == "":
                r = r'.*'

            out[n] = [q,r,d]
        return out
        
    def searchLinks(self):
        ignore = self.get_config("ignore").lower().replace(",","|") if not self.get_config("ignore") == "" else "^unmatchable$"
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".",key).lower()
            for post in self.feed.entries:
                """Search for title"""
                found = re.search(s,post.title.lower())
                if found:
                    """Check if we have to ignore it"""
                    found = re.search(ignore,post.title.lower())
                    if found:
                        self.log_debug("Ignoring [%s]" %post.title)
                        continue
                    """Search for quality"""
                    ss = self.allInfos[key][0].lower()
                    if ss == "480p":
                        if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower():
                            continue
                        found = True
                    else:
                        found = re.search(ss,post.title.lower())
                    if found:
                        """Search for releasegroup"""
                        sss = "[\.-]+"+self.allInfos[key][1].lower()
                        found = re.search(sss,post.title.lower())
                        if found:
                            destination = self.allInfos[key][2].lower()
                            try:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*',post.title.lower()).group(1)
                                if "repack" in post.title.lower():
                                    episode = episode + "-repack"
                                self.log_debug("TV-Series detected, will shorten its name to [%s]" %episode)
                                self.dictWithNamesAndLinks[episode] = [post.link, destination]
                            except:
                                self.dictWithNamesAndLinks[post.title] = [post.link, destination]        
    
    
    def quietHours(self):
        hours = self.get_config("quiethours").split(",")        
        if str(time.localtime()[3]) in hours:
            self.log_debug("Quiet hour, nothing to do!")
            return True
        else:
            return False
    
    def periodical(self):
        if self.quietHours():
            return
            
        urls = []
        text = []
        self.mypatterns = self.readInput()
        
        self.dictWithNamesAndLinks = {}
        self.allInfos = self.getPatterns()
        
        if self.get_config("historical"):
            for xline in self.mypatterns:
                if len(xline) == 0 or xline.startswith("#"):
                    continue
                xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                urls.append('http://www.movie-blog.org/search/%s/feed/rss2/' %xn)
        else:
            urls.append(self.FEED_URL)

        for url in urls:
            self.feed = feedparser.parse(url)
            self.searchLinks()

        for key in self.dictWithNamesAndLinks:
            if not self.retrieve(key) == 'added':
                self.store(key, 'added')
                
                if self.get_config("destination") == self.dictWithNamesAndLinks[key][1] == "collector":
                    destination = 0
                elif self.get_config("destination") == self.dictWithNamesAndLinks[key][1] == "queue":
                    destination = 1
                elif self.dictWithNamesAndLinks[key][1] == "":
                    destination = 1 if self.get_config("destination") == "queue" else 0
                else:
                    destination = 1 if self.dictWithNamesAndLinks[key][1] == "queue" else 0

                self.pyload.api.addPackage(key, [self.dictWithNamesAndLinks[key][0]], destination)
                text.append(key)
            else:
                self.log_debug("[%s] has already been added" %key)
        if len(text) > 0:
            notify(text)
            notifyPushbullet(self.get_config("pushbulletapi"),text)