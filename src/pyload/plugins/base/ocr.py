# -*- coding: utf-8 -*-

import os
import subprocess

from PIL import Image

from pyload import PKGDIR

from .plugin import BasePlugin

# import tempfile


class BaseOCR(BasePlugin):
    __name__ = "BaseOCR"
    __type__ = "base"
    __version__ = "0.26"
    __status__ = "stable"

    __description__ = """OCR base plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad team", "admin@pyload.net")]

    def __init__(self, pyfile):
        self._init(pyfile.m.pyload)
        self.pyfile = pyfile
        self.init()

    def _log(self, level, plugintype, pluginname, args, kwargs):
        args = (self.__name__,) + args
        return self.pyfile.plugin._log(
            level, plugintype, self.pyfile.plugin.__name__, args, kwargs
        )

    def load_image(self, image):
        self.img = Image.open(image)
        self.pixels = self.img.load()
        self.result_captcha = ""

    def deactivate(self):
        """
        Delete all tmp images.
        """
        pass

    def threshold(self, value):
        self.img = self.img.point(lambda a: a * value + 10)

    def call_cmd(self, command, *args, **kwargs):
        """
        Run a command.
        """
        call = [command] + args
        self.log_debug("EXECUTE " + " ".join(call))

        popen = subprocess.Popen(
            call, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        popen.wait()

        output = popen.stdout.read() + " | " + popen.stderr.read()

        popen.stdout.close()
        popen.stderr.close()

        self.log_debug(f"Tesseract ReturnCode {popen.returncode}", f"Output: {output}")

    def run_tesser(
        self,
        subset=False,
        digits=True,
        lowercase=True,
        uppercase=True,
        pagesegmode=None,
    ):
        # tmp_tif = tempfile.NamedTemporaryFile(suffix=".tif")
        try:
            tmp_tif = open(
                os.path.join(self.pyload.tempdir, f"tmp_tif_{self.classname}.tif"),
                mode="wb",
            )
            tmp_tif.close()

            # tmp_txt = tempfile.NamedTemporaryFile(suffix=".txt")
            tmp_txt = open(
                os.path.join(self.pyload.tempdir, f"tmp_txt_{self.classname}.txt"),
                mode="wb",
            )
            tmp_txt.close()

        except IOError as exc:
            self.log_error(exc)
            return

        self.log_debug("Saving tiff...")
        self.img.save(tmp_tif.name, "TIFF")

        if os.name == "nt":
            command = os.path.join(PKGDIR, "lib", "tesseract", "tesseract.exe")
        else:
            command = "tesseract"

        args = [
            os.path.realpath(tmp_tif.name),
            os.path.realpath(tmp_txt.name).replace(".txt", ""),
        ]

        if pagesegmode:
            args.extend(["-psm", str(pagesegmode)])

        if subset and (digits or lowercase or uppercase):
            # tmp_sub = tempfile.NamedTemporaryFile(suffix=".subset")
            with open(
                os.path.join(
                    self.pyload.tempdir, "tmp_sub_{}.subset".format(self.classname)
                ),
                "wb",
            ) as tmp_sub:
                tmp_sub.write("tessedit_char_whitelist ")

                if digits:
                    tmp_sub.write("0123456789")
                if lowercase:
                    tmp_sub.write("abcdefghijklmnopqrstuvwxyz")
                if uppercase:
                    tmp_sub.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

                tmp_sub.write("\n")
                args.append("nobatch")
                args.append(os.path.realpath(tmp_sub.name))

        self.log_debug("Running tesseract...")
        self.call_cmd(command, *args)
        self.log_debug("Reading txt...")

        try:
            with open(tmp_txt.name) as fp:
                self.result_captcha = fp.read().replace("\n", "")

        except Exception:
            self.result_captcha = ""

        self.log_info(self._("OCR result: ") + self.result_captcha)

        self.remove(tmp_tif.name, try_trash=False)
        self.remove(tmp_txt.name, try_trash=False)

        if subset and (digits or lowercase or uppercase):
            self.remove(tmp_sub.name, try_trash=False)

    def recognize(self, image):
        raise NotImplementedError

    def to_greyscale(self):
        if self.img.mode != "L":
            self.img = self.img.convert("L")

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
        Rotate by checking each angle and guess most suitable.
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
