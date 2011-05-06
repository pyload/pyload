import re

class ReCaptcha():
    def __init__(self, plugin):
        self.plugin = plugin
    
    def challenge(self, id):
        js = self.plugin.req.load("http://www.google.com/recaptcha/api/challenge", get={"k":id}, cookies=True)
        
        try:
            challenge = re.search("challenge : '(.*?)',", js).group(1)
            server = re.search("server : '(.*?)',", js).group(1)
        except:
            self.plugin.fail("recaptcha error")
        result = self.result(server,challenge)
        
        return challenge, result

    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%simage"%server, get={"c":challenge}, cookies=True, imgtype="jpg")
        
