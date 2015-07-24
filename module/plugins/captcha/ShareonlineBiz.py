# -*- coding: utf-8 -*-

from module.plugins.internal.OCR import OCR


class ShareonlineBiz(OCR):
    __name__    = "ShareonlineBiz"
    __type__    = "ocr"
    __version__ = "0.14"
    __status__  = "testing"

    __description__ = """Shareonline.biz ocr plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def recognize(self, image):
        self.load_image(image)
        self.to_greyscale()
        self.image = self.image.resize((160, 50))
        self.pixels = self.image.load()
        self.threshold(1.85)
        # self.eval_black_white(240)
        # self.derotate_by_average()

        letters = self.split_captcha_letters()

        final = ""
        for letter in letters:
            self.image = letter
            self.run_tesser(True, True, False, False)
            final += self.result_captcha

        return final

        #: Tesseract at 60%
