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
from __future__ import with_statement
import os
from os.path import join
from os.path import abspath
import logging
import subprocess
#import tempfile

import Image
import TiffImagePlugin
import PngImagePlugin
import GifImagePlugin
import JpegImagePlugin


class OCR(object):
    __version__ = 0.1
    
    def __init__(self):
        self.logger = logging.getLogger("log")

    def load_image(self, image):
        self.image = Image.open(image)
        self.pixels = self.image.load()
        self.result_captcha = ''

    def unload(self):
        """delete all tmp images"""
        pass

    def threshold(self, value):
        self.image = self.image.point(lambda a: a * value + 10)

    def run(self, command):
        """Run a command"""
            
        popen = subprocess.Popen(command, bufsize = -1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        popen.wait()
        output = popen.stdout.read() +" | "+ popen.stderr.read()
        popen.stdout.close()
        popen.stderr.close()
        self.logger.debug("Tesseract ReturnCode %s Output: %s" % (popen.returncode, output))

    def run_tesser(self, subset=False, digits=True, lowercase=True, uppercase=True):
        #self.logger.debug("create tmp tif")
        
        
        #tmp = tempfile.NamedTemporaryFile(suffix=".tif")
        tmp = open(join("tmp", "tmpTif_%s.tif" % self.__name__), "wb")
        tmp.close()
        #self.logger.debug("create tmp txt")
        #tmpTxt = tempfile.NamedTemporaryFile(suffix=".txt")
        tmpTxt = open(join("tmp", "tmpTxt_%s.txt" % self.__name__), "wb")
        tmpTxt.close()
        
        self.logger.debug("save tiff")
        self.image.save(tmp.name, 'TIFF')

        if os.name == "nt":
            tessparams = [join(pypath,"tesseract","tesseract.exe")]
        else:
            tessparams = ['tesseract']
        
        tessparams.extend( [abspath(tmp.name), abspath(tmpTxt.name).replace(".txt", "")] )

        if subset and (digits or lowercase or uppercase):
            #self.logger.debug("create temp subset config")
            #tmpSub = tempfile.NamedTemporaryFile(suffix=".subset")
            tmpSub = open(join("tmp", "tmpSub_%s.subset" % self.__name__), "wb")
            tmpSub.write("tessedit_char_whitelist ")
            if digits:
                tmpSub.write("0123456789")
            if lowercase:
                tmpSub.write("abcdefghijklmnopqrstuvwxyz")
            if uppercase:
                tmpSub.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            tmpSub.write("\n")
            tessparams.append("nobatch")
            tessparams.append(abspath(tmpSub.name))
            tmpSub.close()
            
        self.logger.debug("run tesseract")
        self.run(tessparams)
        self.logger.debug("read txt")

        try:
            with open(tmpTxt.name, 'r') as f:
                self.result_captcha = f.read().replace("\n", "")
        except:
            self.result_captcha = ""

        self.logger.debug(self.result_captcha)
        try:
            os.remove(tmp.name)
            os.remove(tmpTxt.name)
            if subset and (digits or lowercase or uppercase):
                os.remove(tmpSub.name)
        except:
            pass
        
    def get_captcha(self, name):
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
                    if not started:
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

    def correct(self, values, var=None):

        if var:
            result = var
        else:
            result = self.result_captcha

        for key, item in values.iteritems():

            if key.__class__ == str:
                result = result.replace(key, item)
            else:
                for expr in key:
                    result = result.replace(expr, item)

        if var:
            return result
        else:
            self.result_captcha = result


if __name__ == '__main__':
    ocr = OCR()
    ocr.load_image("B.jpg")
    ocr.to_greyscale()
    ocr.eval_black_white(140)
    ocr.derotate_by_average()
    ocr.run_tesser()
    print "Tesseract", ocr.result_captcha
    ocr.image.save("derotated.jpg")
    
