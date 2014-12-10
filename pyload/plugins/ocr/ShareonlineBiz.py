# -*- coding: utf-8 -*-

from pyload.plugins.OCR import OCR


class ShareonlineBiz(OCR):
    __name    = "ShareonlineBiz"
    __type    = "ocr"
    __version = "0.10"

    __description = """Shareonline.biz ocr plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def __init__(self):
        OCR.__init__(self)


    def get_captcha(self, image):
        self.load_image(image)
        self.to_greyscale()
        self.image = self.image.resize((160, 50))
        self.pixels = self.image.load()
        self.threshold(1.85)
        #self.eval_black_white(240)
        #self.derotate_by_average()

        letters = self.split_captcha_letters()

        final = ""
        for letter in letters:
            self.image = letter
            self.run_tesser(True, True, False, False)
            final += self.result_captcha

        return final

        #tesseract at 60%
