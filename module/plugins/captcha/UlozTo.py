# -*- coding: utf-8 -*-

import os.path

from ..internal.OCR import OCR

try:
    import adecaptcha.clslib as clslib
except ImportError:
    pass


class UlozTo(OCR):
    __name__ = "UlozTo"
    __type__ = "captcha"
    __version__ = "0.05"
    __status__ = "testing"

    __description__ = """UlozTo audio captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("sodd", None),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def recognize(self, audio):
        """ Audio decoding - more info could be found at https://launchpad.net/adecaptcha """
        # print("!!!CAPTCHA :", audio)
        try:
            cfg_file = os.path.join(
                os.path.split(
                    clslib.__file__)[0],
                'ulozto.cfg')
            ext_file = os.path.splitext(audio)[1]
            text = clslib.classify_audio_file(audio, cfg_file, ext_file)
            return text

        except NameError:
            self.log_error(_("Unable to decode audio captcha"),
                           _("Please install adecaptcha library from https://github.com/izderadicka/adecaptcha"))
