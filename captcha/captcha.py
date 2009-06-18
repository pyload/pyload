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
import subprocess
import tempfile

import Image
import ImageOps

class OCR(object):
    def __init__(self):
        pass

    def load_image(self, image):
        self.image = Image.open(image)
        self.pixels = self.image.load()
        self.result_captcha = ''

    def unload(self):
        """delete all tmp images"""
        pass

    def threshold(self, value):
        self.image = self.image.point(lambda a: a * value + 10)

    def run(self, command, inputdata=None):
        """Run a command and return standard output"""
        pipe = subprocess.PIPE
        popen = subprocess.Popen(command, stdout=pipe, stderr=pipe)
        outputdata, errdata = popen.communicate(inputdata)
        assert (popen.returncode == 0), \
            "Error running: %s\n\n%s" % (command, errdata)
        return outputdata

    def run_gocr(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg")
        self.image.save(tmp)
        self.result_captcha = self.run(['gocr', tmp.name]).replace("\n", "")

    def run_tesser(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".tif")
        tmpTxt = tempfile.NamedTemporaryFile(suffix=".txt")

        self.image.save(tmp.name, 'TIFF')
        self.run(['tesseract', tmp.name, tmpTxt.name.replace(".txt", "")])

        self.result_captcha = self.run(['cat', tmpTxt.name])

    def get_captcha(self):
        raise NotImplementedError

    def to_greyscale(self):
        if self.image.mode != 'L':
            self.image = self.image.convert('L')

        self.pixels = self.image.load()


    def clean(self, allowed):
        pixels = self.pixels

        w, h = self.image.size

        for x in xrange(w):
            for y in xrange(h):
                if pixels[x, y] == 255: continue
                # no point in processing white pixels since we only want to remove black pixel
                count = 0

                try:
                    if pixels[x-1, y-1] != 255: count += 1
                    if pixels[x-1, y] != 255: count += 1
                    if pixels[x-1, y + 1] != 255: count += 1
                    if pixels[x, y + 1] != 255: count += 1
                    if pixels[x + 1, y + 1] != 255: count += 1
                    if pixels[x + 1, y] != 255: count += 1
                    if pixels[x + 1, y-1] != 255: count += 1
                    if pixels[x, y-1] != 255: count += 1
                except:
                    pass

        # not enough neighbors are dark pixels so mark this pixel
            # to be changed to white
                if count < allowed:
                    pixels[x, y] = 1

            # second pass: this time set all 1's to 255 (white)
        for x in xrange(w):
            for y in xrange(h):
                if pixels[x, y] == 1: pixels[x, y] = 255

        self.pixels = pixels


if __name__ == '__main__':
    ocr = OCR('gigasize-com/7.jpg')
    print  ocr.get_captcha()
