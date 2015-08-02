# -*- coding: utf-8 -*-

from __future__ import with_statement

try:
    from PIL import Image, GifImagePlugin, JpegImagePlugin, PngImagePlugin, TiffImagePlugin

except ImportError:
    import Image, GifImagePlugin, JpegImagePlugin, PngImagePlugin, TiffImagePlugin

import logging
import os
import subprocess
# import tempfile
import traceback

from module.plugins.internal.Plugin import Plugin
from module.utils import save_join as fs_join


class OCR(Plugin):
    __name__    = "OCR"
    __type__    = "ocr"
    __version__ = "0.19"
    __status__  = "testing"

    __description__ = """OCR base plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    def __init__(self, plugin):
        self._init(plugin.pyload)
        self.plugin = plugin
        self.init()


    def init(self):
        """
        Initialize additional data structures
        """
        pass


    def _log(self, level, plugintype, pluginname, messages):
        return self.plugin._log(level,
                                plugintype,
                                self.plugin.__name__,
                                (self.__name__,) + messages)


    def load_image(self, image):
        self.image = Image.open(image)
        self.pixels = self.image.load()
        self.result_captcha = ""


    def deactivate(self):
        """
        Delete all tmp images
        """
        pass


    def threshold(self, value):
        self.image = self.image.point(lambda a: a * value + 10)


    def run(self, command):
        """
        Run a command
        """
        popen = subprocess.Popen(command, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        popen.wait()
        output = popen.stdout.read() + " | " + popen.stderr.read()
        popen.stdout.close()
        popen.stderr.close()
        self.pyload.log_debug("Tesseract ReturnCode " + popen.returncode, "Output: " + output)


    def run_tesser(self, subset=False, digits=True, lowercase=True, uppercase=True, pagesegmode=None):
        # tmpTif = tempfile.NamedTemporaryFile(suffix=".tif")
        try:
            tmpTif = open(fs_join("tmp", "tmpTif_%s.tif" % self.__name__), "wb")
            tmpTif.close()

            # tmpTxt = tempfile.NamedTemporaryFile(suffix=".txt")
            tmpTxt = open(fs_join("tmp", "tmpTxt_%s.txt" % self.__name__), "wb")
            tmpTxt.close()

        except IOError, e:
            self.log_error(e)
            return

        self.pyload.log_debug("Saving tiff...")
        self.image.save(tmpTif.name, 'TIFF')

        if os.name == "nt":
            tessparams = [os.path.join(pypath, "tesseract", "tesseract.exe")]
        else:
            tessparams = ["tesseract"]

        tessparams.extend([os.path.abspath(tmpTif.name), os.path.abspath(tmpTxt.name).replace(".txt", "")])

        if pagesegmode:
            tessparams.extend(["-psm", str(pagesegmode)])

        if subset and (digits or lowercase or uppercase):
            # tmpSub = tempfile.NamedTemporaryFile(suffix=".subset")
            with open(fs_join("tmp", "tmpSub_%s.subset" % self.__name__), "wb") as tmpSub:
                tmpSub.write("tessedit_char_whitelist ")

                if digits:
                    tmpSub.write("0123456789")
                if lowercase:
                    tmpSub.write("abcdefghijklmnopqrstuvwxyz")
                if uppercase:
                    tmpSub.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

                tmpSub.write("\n")
                tessparams.append("nobatch")
                tessparams.append(os.path.abspath(tmpSub.name))

        self.pyload.log_debug("Running tesseract...")
        self.run(tessparams)
        self.pyload.log_debug("Reading txt...")

        try:
            with open(tmpTxt.name, 'r') as f:
                self.result_captcha = f.read().replace("\n", "")
        except Exception:
            self.result_captcha = ""

        self.pyload.log_info(_("OCR result: ") + self.result_captcha)
        try:
            os.remove(tmpTif.name)
            os.remove(tmpTxt.name)
            if subset and (digits or lowercase or uppercase):
                os.remove(tmpSub.name)
        except OSError, e:
            self.log_warning(e)
            if self.pyload.debug:
                traceback.print_exc()


    def recognize(self, name):
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
                if pixels[x, y] == 255:
                    continue
                #: No point in processing white pixels since we only want to remove black pixel
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

                #: Not enough neighbors are dark pixels so mark this pixel
                #: To be changed to white
                if count < allowed:
                    pixels[x, y] = 1

        #: Second pass: this time set all 1's to 255 (white)
        for x in xrange(w):
            for y in xrange(h):
                if pixels[x, y] == 1:
                    pixels[x, y] = 255

        self.pixels = pixels


    def derotate_by_average(self):
        """
        Rotate by checking each angle and guess most suitable
        """
        w, h = self.image.size
        pixels = self.pixels

        for x in xrange(w):
            for y in xrange(h):
                if pixels[x, y] == 0:
                    pixels[x, y] = 155

        highest = {}
        counts = {}

        for angle in xrange(-45, 45):

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

        for key, value in highest.items():
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

                    if y > bottomY:
                        bottomY = y
                    if y < topY:
                        topY = y
                    if x > lastX:
                        lastX = x

                    black_pixel_in_col = True

            if black_pixel_in_col is False and started is True:
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

        for key, item in values.items():

            if key.__class__ is str:
                result = result.replace(key, item)
            else:
                for expr in key:
                    result = result.replace(expr, item)

        if var:
            return result
        else:
            self.result_captcha = result
