# -*- coding: utf-8 -*-

#
# Copyright (C) 2009 kingzero, RaNaN
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#

# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, unicode_literals

import logging
import os
from builtins import object, range

from future import standard_library
from pkg_resources import resource_filename

import Image
from pyload.utils.fs import lopen, remove
from pyload.utils.layer.legacy.subprocess_ import PIPE, Popen

from ..__about__ import __package__

standard_library.install_aliases()


# import tempfile


class OCR(object):
    __version__ = 0.1

    def __init__(self):
        self.log = logging.getLogger()

    def load_image(self, image):
        self.image = Image.open(image)
        self.pixels = self.image.load()
        self.result_captcha = ''

    def unload(self):
        """
        Delete all tmp images.
        """
        pass

    def threshold(self, value):
        self.image = self.image.point(lambda a: a * value + 10)

    def run(self, command):
        """
        Run a command.
        """
        popen = Popen(
            command, bufsize=-1, stdout=PIPE, stderr=PIPE)
        popen.wait()
        output = "{0} | {1}".format(popen.stdout.read(), popen.stderr.read())
        popen.stdout.close()
        popen.stderr.close()
        self.log.debug("Tesseract ReturnCode {0} Output: {1}".format(
            popen.returncode, output))

    def run_tesser(self, subset=False, digits=True,
                   lowercase=True, uppercase=True):
        # self.log.debug("create tmp tif")

        # tmp = tempfile.NamedTemporaryFile(suffix=".tif")
        tmp_path = os.path.join("tmpTif_{0}.tif".format(self.__name__))
        tmp = lopen(tmp_path, mode='wb')
        tmp.close()
        # self.log.debug("create tmp txt")
        # tmp_txt = tempfile.NamedTemporaryFile(suffix=".txt")
        tmp_txt_path = os.path.join("tmp_txt_{0}.txt".format(
            self.__name__))
        tmp_txt = lopen(tmp_txt_path, mode='wb')
        tmp_txt.close()

        self.log.debug("save tiff")
        self.image.save(tmp.name, 'TIFF')

        if os.name == 'nt':
            tessparams = [resource_filename(
                __package__, 'tesseract/tesseract.exe')]
        else:
            tessparams = ['tesseract']

        tessparams.extend([tmp.name, tmp_txt.name.replace(".txt", "")])

        if subset and (digits or lowercase or uppercase):
            # self.log.debug("create temp subset config")
            # tmp_sub = tempfile.NamedTemporaryFile(suffix=".subset")
            with lopen(os.path.join("tmp_sub_{0}.subset".format(self.__name__)), mode='wb') as tmp_sub:
                tmp_sub.write("tessedit_char_whitelist ")
                if digits:
                    tmp_sub.write("0123456789")
                if lowercase:
                    tmp_sub.write("abcdefghijklmnopqrstuvwxyz")
                if uppercase:
                    tmp_sub.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                tmp_sub.write(os.linesep)
                tessparams.append("nobatch")
                tessparams.append(tmp_sub.name)

        self.log.debug("run tesseract")
        self.run(tessparams)
        self.log.debug("read txt")

        try:
            with lopen(tmp_txt.name) as fp:
                self.result_captcha = fp.read().replace(os.linesep, "")
        except Exception:
            self.result_captcha = ""

        self.log.debug(self.result_captcha)
        try:
            remove(tmp.name)
            remove(tmp_txt.name)
            if subset and (digits or lowercase or uppercase):
                remove(tmp_sub.name)
        except Exception:
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
        for x in range(w):
            for y in range(h):
                if self.pixels[x, y] > limit:
                    self.pixels[x, y] = 255
                else:
                    self.pixels[x, y] = 0

    def clean(self, allowed):
        pixels = self.pixels

        w, h = self.image.size

        for x in range(w):
            for y in range(h):
                if pixels[x, y] == 255:
                    continue
                # no point in processing white pixels since we only want to
                # remove black pixel
                count = 0

                try:
                    if pixels[x - 1, y - 1] != 255:
                        count += 1
                    if pixels[x - 1, y] != 255:
                        count += 1
                    if pixels[x - 1, y + 1] != 255:
                        count += 1
                    if pixels[x, y + 1] != 255:
                        count += 1
                    if pixels[x + 1, y + 1] != 255:
                        count += 1
                    if pixels[x + 1, y] != 255:
                        count += 1
                    if pixels[x + 1, y - 1] != 255:
                        count += 1
                    if pixels[x, y - 1] != 255:
                        count += 1
                except Exception:
                    pass

        # not enough neighbors are dark pixels so mark this pixel
            # to be changed to white
                if count < allowed:
                    pixels[x, y] = 1

            # second pass: this time set all 1's to 255 (white)
        for x in range(w):
            for y in range(h):
                if pixels[x, y] == 1:
                    pixels[x, y] = 255

        self.pixels = pixels

    def derotate_by_average(self):
        """
        Rotate by checking each angle and guess most suitable.
        """
        w, h = self.image.size
        pixels = self.pixels

        for x in range(w):
            for y in range(h):
                if pixels[x, y] == 0:
                    pixels[x, y] = 155

        highest = {}
        counts = {}

        for angle in range(-45, 45):

            tmpimage = self.image.rotate(angle)

            pixels = tmpimage.load()

            w, h = self.image.size

            for x in range(w):
                for y in range(h):
                    if pixels[x, y] == 0:
                        pixels[x, y] = 255

            count = {}

            for x in range(w):
                count[x] = 0
                for y in range(h):
                    if pixels[x, y] == 155:
                        count[x] += 1

            sum = 0
            cnt = 0

            for x in count.values():
                if x != 0:
                    sum += x
                    cnt += 1

            avg = sum // cnt
            counts[angle] = cnt
            highest[angle] = 0
            for x in count.values():
                if x > highest[angle]:
                    highest[angle] = x

            highest[angle] = highest[angle] - avg

        hkey = 0
        hvalue = 0

        for key, value in highest.items():
            if value > hvalue:
                hkey = key
                hvalue = value

        self.image = self.image.rotate(hkey)
        pixels = self.image.load()

        for x in range(w):
            for y in range(h):
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
        bottom_y, top_y = 0, height
        pixels = captcha.load()

        for x in range(width):
            black_pixel_in_col = False
            for y in range(height):
                if pixels[x, y] != 255:
                    if not started:
                        started = True
                        first_x = x
                        last_x = x

                    if y > bottom_y:
                        bottom_y = y
                    if y < top_y:
                        top_y = y
                    if x > last_x:
                        last_x = x

                    black_pixel_in_col = True

            if black_pixel_in_col is False and started is True:
                rect = (first_x, top_y, last_x, bottom_y)
                new_captcha = captcha.crop(rect)

                w, h = new_captcha.size
                if w > 5 and h > 5:
                    letters.append(new_captcha)

                started = False
                bottom_y, top_y = 0, height

        return letters

    def correct(self, values, var=None):

        if var:
            result = var
        else:
            result = self.result_captcha

        for key, item in values.items():

            if key.__class__ == str:
                result = result.replace(key, item)
            else:
                for expr in key:
                    result = result.replace(expr, item)

        if var:
            return result
        else:
            self.result_captcha = result
