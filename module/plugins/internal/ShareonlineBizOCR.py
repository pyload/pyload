#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2009 kingzero, RaNaN
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License,
#or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
###
from OCR import OCR

class ShareonlineBizOCR(OCR):
    __version__ = 0.1
    
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

if __name__ == '__main__':
    import urllib
    ocr = ShareonlineBizOCR()
    urllib.urlretrieve("http://www.share-online.biz/captcha.php", "captcha.jpeg")
    print  ocr.get_captcha('captcha.jpeg')
