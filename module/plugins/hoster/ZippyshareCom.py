# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

from module.lib.BeautifulSoup import BeautifulSoup

class ZippyshareCom(SimpleHoster):
    __name__    = "ZippyshareCom"
    __type__    = "hoster"
    __version__ = "0.74"

    __pattern__ = r'http://www\d{0,2}\.zippyshare\.com/v(/|iew\.jsp.*key=)(?P<KEY>[\w^_]+)'

    __description__ = """Zippyshare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com", "sebdelsol")]


    COOKIES = [("zippyshare.com", "ziplocale", "en")]

    NAME_PATTERN    = r'("\d{6,}/"[ ]*\+.+?"/|<title>Zippyshare.com - )(?P<N>.+?)("|</title>)'
    SIZE_PATTERN    = r'>Size:.+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File does not exist on this server'

    LINK_PREMIUM_PATTERN = r'document.location = \'(.+?)\''


    def setup(self):
        self.chunkLimit     = -1
        self.multiDL        = True
        self.resumeDownload = True


    def handleFree(self, pyfile):
        recaptcha   = ReCaptcha(self)
        captcha_key = recaptcha.detect_key()

        if captcha_key:
            try:
                self.link = re.search(self.LINK_PREMIUM_PATTERN, self.html)
                recaptcha.challenge()

            except Exception, e:
                self.error(e)

        else:
            self.link = self.get_link()

    def get_link(self):
        try:
            # get all the scripts inside the html body
            soup = BeautifulSoup(self.html)
            scripts = (s.getText() for s in soup.body.findAll('script', type='text/javascript'))

            # meant to be populated with the initialization of all the DOM elements found in the scripts
            initScripts = set()
            
            def replElementById(element):
                id, attr = element.group(1), element.group(4)      # attr might be None
            
                varName = '%s_%s' %(id, attr)
            
                initValues = (elt.get(attr, None) for elt in soup.findAll(id=id))
                initValues = [v for v in initValues if v is not None]
                initValue = '"%s"' %initValues[-1] if initValues else 'null'
            
                initScripts.add('var %s = %s;' %(varName, initValue))
                return varName
            
            # handle all getElementById
            reVar = r'document.getElementById\([\'"](\w+)[\'"]\)(\.)?(getAttribute\([\'"])?(\w+)?([\'"]\))?'
            scripts = [re.sub(reVar, replElementById, script) for script in scripts]
            
            # add try/catch in JS to handle deliberate errors
            tryJS, catchJS =  u'try{', u'} catch(err){}' # '', '' to see where the script fails
            scripts = ['\n'.join((tryJS, script, catchJS)) for script in scripts if script.strip()]

            # get the file's url by evaluating all the scripts
            scripts = '\n'.join(list(initScripts) + scripts + ['dlbutton_href'])
            return self.js.eval(scripts)

        except Exception:
            self.error(_("Unable to calculate the link"))

getInfo = create_getInfo(ZippyshareCom)
