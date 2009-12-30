# -*- coding: utf-8 -*-

import re
from time import sleep

from module.Plugin import Plugin
from module.BeautifulSoup import BeautifulSoup

class SerienjunkiesOrg(Plugin):
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "SerienjunkiesOrg"
        props['type'] = "container"
        props['pattern'] = r"http://.*?serienjunkies.org/.*?"
        props['version'] = "0.1"
        props['description'] = """serienjunkies.org Container Plugin"""
        props['author_name'] = ("mkaay")
        props['author_mail'] = ("mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.html = None
        self.multi_dl = False
    
    def getSJSrc(self, url):
        src = self.req.load(str(url))
        if not src.find("Enter Serienjunkies") == -1:
            src = self.req.load(str(url))
        return src
    
    def file_exists(self):
        return True
    
    def handleEpisode(self, url):
        if not self.parent.core.isGUIConnected():
            return False
        for i in range(3):
            src = self.getSJSrc(url)
            if not src.find("Du hast das Download-Limit &uuml;berschritten! Bitte versuche es sp&auml;ter nocheinmal.") == -1:
                self.logger.info("Downloadlimit reached")
                return False
            else:
                soup = BeautifulSoup(src)
                form = soup.find("form")
                captchaTag = soup.find(attrs={"src":re.compile("^/secure/")})
                captchaUrl = "http://download.serienjunkies.org"+captchaTag["src"]
                captchaData = self.req.load(str(captchaUrl))
                captchaManager = self.parent.core.captchaManager
                task = captchaManager.newTask(self)
                task.setCaptcha(captchaData, "png")
                task.setWaiting()
                while not task.getStatus() == "done":
                    if not self.parent.core.isGUIConnected():
                        task.removeTask()
                        return False
                    sleep(1)
                result = task.getResult()
                task.removeTask()
                url = "http://download.serienjunkies.org"+form["action"]
                sinp = form.find(attrs={"name":"s"})
                
                sj = self.req.load(str(url), post={'s': sinp["value"], 'c': result, 'action': "Download"})
                
                soup = BeautifulSoup(sj)
                rawLinks = soup.findAll(attrs={"action": re.compile("^http://download.serienjunkies.org/")})
                
                if not len(rawLinks) > 0:
                    continue
                
                links = []
                for link in rawLinks:
                    frameUrl = link["action"].replace("/go-", "/frame/go-")
                    links.append(self.handleFrame(frameUrl))
                return links
    
    def handleFrame(self, url):
        self.req.load(str(url), cookies=False, just_header=True)
        return self.req.lastEffectiveURL
    
    def proceed(self, url, location):
        links = False
        episodePattern = re.compile("^http://download.serienjunkies.org/f-.*?.html$")
        framePattern = re.compile("^http://download.serienjunkies.org/frame/go-.*?/$")
        if framePattern.match(url):
            links = [self.handleFrame(url)]
        elif episodePattern.match(url):
            links = self.handleEpisode(url)
        self.links = links
