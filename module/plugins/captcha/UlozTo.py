try:
        import adecaptcha.clslib as clslib
        adecaptcha_available = True
except ImportError:
        adecaptcha_available = False

import os.path



class UlozTo(object):
    __name__ = "UlozTo"
    def __init__(self, plugin=None):
        pass
        self._plugin=plugin


    def recognize(self, audio):
        """ Audio decoding - more info could be found at https://launchpad.net/adecaptcha """
        #print "!!!CAPTCHA :", audio
        if adecaptcha_available:
                cfg_file=os.path.join(os.path.split(clslib.__file__)[0], 'ulozto.cfg')
                text= clslib.classify_audio_file(audio, cfg_file)
                return text
        else:
                pass
