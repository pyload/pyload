# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import subprocess

from .misc import encode, fsjoin
from .Plugin import Plugin

try:
    from PIL import Image

except ImportError:
    import Image

# import tempfile


class OCR(Plugin):
    __name__ = "OCR"
    __type__ = "ocr"
    __version__ = "0.26"
    __status__ = "stable"

    __description__ = """OCR base plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad Team", "admin@pyload.org")]

    def __init__(self, pyfile):
        self._init(pyfile.m.core)
        self.pyfile = pyfile
        self.init()

    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.__name__,) + messages
        return self.pyfile.plugin._log(
            level, plugintype, self.pyfile.plugin.__name__, messages)

    def load_image(self, image):
        self.img = Image.open(image)
        self.pixels = self.img.load()
        self.result_captcha = ""

    def deactivate(self):
        """
        Delete all tmp images
        """
        pass

    def threshold(self, value):
        self.img = self.img.point(lambda a: a * value + 10)

    def call_cmd(self, command, *args, **kwargs):
        """
        Run a command
        """
        call = (command,) + args
        self.log_debug("EXECUTE " + " ".join(call))

        call = map(encode, call)
        popen = subprocess.Popen(
            call,
            bufsize=-1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        popen.wait()

        output = popen.stdout.read() + " | " + popen.stderr.read()

        popen.stdout.close()
        popen.stderr.close()

        self.log_debug(
            "Tesseract ReturnCode %d" %
            popen.returncode,
            "Output: %s" %
            output)

    def run_tesser(self, subset=False, digits=True,
                   lowercase=True, uppercase=True, pagesegmode=None):
        # tmpTif = tempfile.NamedTemporaryFile(suffix=".tif")
        try:
            tmpTif = open(
                fsjoin(
                    "tmp",
                    "tmpTif_%s.tif" %
                    self.classname),
                "wb")
            tmpTif.close()

            # tmpTxt = tempfile.NamedTemporaryFile(suffix=".txt")
            tmpTxt = open(
                fsjoin(
                    "tmp",
                    "tmpTxt_%s.txt" %
                    self.classname),
                "wb")
            tmpTxt.close()

        except IOError, e:
            self.log_error(e)
            return

        self.log_debug("Saving tiff...")
        self.img.save(tmpTif.name, 'TIFF')

        if os.name == "nt":
            command = os.path.join(pypath, "tesseract", "tesseract.exe")
        else:
            command = "tesseract"

        args = [
            os.path.abspath(
                tmpTif.name),
            os.path.abspath(
                tmpTxt.name).replace(
                ".txt",
                "")]

        if pagesegmode:
            args.extend(["-psm", str(pagesegmode)])

        if subset and (digits or lowercase or uppercase):
            # tmpSub = tempfile.NamedTemporaryFile(suffix=".subset")
            with open(fsjoin("tmp", "tmpSub_%s.subset" % self.classname), "wb") as tmpSub:
                tmpSub.write("tessedit_char_whitelist ")

                if digits:
                    tmpSub.write("0123456789")
                if lowercase:
                    tmpSub.write("abcdefghijklmnopqrstuvwxyz")
                if uppercase:
                    tmpSub.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

                tmpSub.write("\n")
                args.append("nobatch")
                args.append(os.path.abspath(tmpSub.name))

        self.log_debug("Running tesseract...")
        self.call_cmd(command, *args)
        self.log_debug("Reading txt...")

        try:
            with open(tmpTxt.name, 'r') as f:
                self.result_captcha = f.read().replace("\n", "")

        except Exception:
            self.result_captcha = ""

        self.log_info(_("OCR result: ") + self.result_captcha)

        self.remove(tmpTif.name, trash=False)
        self.remove(tmpTxt.name, trash=False)

        if subset and (digits or lowercase or uppercase):
            self.remove(tmpSub.name, trash=False)

    def recognize(self, image):
        raise NotImplementedError

    def to_greyscale(self):
        if self.img.mode != 'L':
            self.img = self.img.convert('L')

        self.pixels = self.img.load()

    def eval_black_white(self, limit):
        self.pixels = self.img.load()
        w, h = self.img.size
        for x in range(w):
            for y in range(h):
                if self.pixels[x, y] > limit:
                    self.pixels[x, y] = 255
                else:
                    self.pixels[x, y] = 0

    def clean(self, allowed):
        pixels = self.pixels

        w, h = self.img.size

        for x in range(w):
            for y in range(h):
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
        for x in range(w):
            for y in range(h):
                if pixels[x, y] == 1:
                    pixels[x, y] = 255

        self.pixels = pixels

    def derotate_by_average(self):
        """
        Rotate by checking each angle and guess most suitable
        """
        w, h = self.img.size
        pixels = self.pixels

        for x in range(w):
            for y in range(h):
                if pixels[x, y] == 0:
                    pixels[x, y] = 155

        highest = {}
        counts = {}

        for angle in range(-45, 45):

            tmpimage = self.img.rotate(angle)

            pixels = tmpimage.load()

            w, h = self.img.size

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

        self.img = self.img.rotate(hkey)
        pixels = self.img.load()

        for x in range(w):
            for y in range(h):
                if pixels[x, y] == 0:
                    pixels[x, y] = 255

                if pixels[x, y] == 155:
                    pixels[x, y] = 0

        self.pixels = pixels

    def split_captcha_letters(self):
        captcha = self.img
        started = False
        letters = []
        width, height = captcha.size
        bottomY, topY = 0, height
        pixels = captcha.load()

        for x in range(width):
            black_pixel_in_col = False
            for y in range(height):
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
