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

        self.result_captcha = self.run(['cat', tmpTxt.name]).replace("\n", "")

    def get_captcha(self):
        raise NotImplementedError

    def to_greyscale(self):
        if self.image.mode != 'L':
            self.image = self.image.convert('L')

        self.pixels = self.image.load()

    def eval_black_white(self, limit):
        self.pixels = self.image.load()
        w, h = self.image.size
        for x in xrange(w):
            for y in xrange(h):
                if self.pixels[x, y] > limit:
                    self.pixels[x, y] = 255
                else:
                    self.pixels[x, y] = 0

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

    def derotate_by_average(self):
        """rotate by checking each angle and guess most suitable"""

        w, h = self.image.size
        pixels = self.pixels

        for x in xrange(w):
            for y in xrange(h):
                if pixels[x, y] == 0:
                    pixels[x, y] = 155

        highest = {}
        counts = {}

        for angle in range(-45, 45):

            tmpimage = self.image.rotate(angle)
        
            pixels = tmpimage.load()

            w, h = self.image.size

            for x in xrange(w):
                for y in xrange(h):
                    if pixels[x, y] == 0:
                        pixels[x, y] = 255


            count = {}

            for x in xrange(w):
                count[x] = 0
                for y in xrange(h):
                    if pixels[x, y] == 155:
                        count[x] += 1

            sum = 0
            cnt = 0

            for x in count.values():
                if x != 0:
                    sum += x
                    cnt += 1

            avg = sum / cnt
            counts[angle] = cnt
            highest[angle] = 0
            for x in count.values():
                if x > highest[angle]:
                    highest[angle] = x

            highest[angle] = highest[angle] - avg

        hkey = 0
        hvalue = 0

        for key, value in highest.iteritems():
            if value > hvalue:
                hkey = key
                hvalue = value

        self.image = self.image.rotate(hkey)
        pixels = self.image.load()

        for x in xrange(w):
            for y in xrange(h):
                if pixels[x, y] == 0:
                    pixels[x, y] = 255

                if pixels[x, y] == 155:
                    pixels[x, y] = 0

        self.pixels = pixels

    def split_captcha_letters(self):
        captcha = self.image
        started = False
        letters = []
        width, height = captcha.size
        bottomY, topY = 0, height
        pixels = captcha.load()
  
        for x in xrange(width):
            black_pixel_in_col = False
            for y in xrange(height):
                if pixels[x, y] != 255:
                    if started == False:
                        started = True
                        firstX = x
                        lastX = x
   
                    if y > bottomY: bottomY = y
                    if y < topY: topY = y
                    if x > lastX: lastX = x
   
                    black_pixel_in_col = True
   
            if black_pixel_in_col == False and started == True:
                rect = (firstX, topY, lastX, bottomY)
                new_captcha = captcha.crop(rect)

                w, h = new_captcha.size
                if w > 5 and h > 5:
                    letters.append(new_captcha)
  
                started = False
                bottomY, topY = 0, height
  
        return letters


        
if __name__ == '__main__':
    ocr = OCR()
    ocr.load_image("B.jpg")
    ocr.to_greyscale()
    ocr.eval_black_white(140)
    ocr.derotate_by_avergage()
    ocr.run_gocr()
    print "GOCR", ocr.result_captcha
    ocr.run_tesser()
    print "Tesseract", ocr.result_captcha
    ocr.image.save("derotated.jpg")
    
