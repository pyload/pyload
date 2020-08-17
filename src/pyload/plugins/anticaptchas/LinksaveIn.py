# -*- coding: utf-8 -*-

import glob
import os

from PIL import Image

from ..base.ocr import BaseOCR


class LinksaveIn(BaseOCR):
    __name__ = "LinksaveIn"
    __type__ = "ocr"
    __version__ = "0.19"
    __status__ = "testing"

    __description__ = """Linksave.in ocr plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad team", "admin@pyload.net")]

    def init(self):
        self.data_dir = os.path.dirname(__file__) + os.sep + "LinksaveIn" + os.sep

    def load_image(self, image):
        im = Image.open(image)
        frame_nr = 0

        lut = im.resize((256, 1))
        lut.putdata(list(range(256)))
        lut = list(lut.convert("RGB").getdata())

        new = Image.new("RGB", im.size)
        npix = new.load()
        while True:
            try:
                im.seek(frame_nr)
            except EOFError:
                break
            frame = im.copy()
            pix = frame.load()
            for x in range(frame.size[0]):
                for y in range(frame.size[1]):
                    if lut[pix[x, y]] != (0, 0, 0):
                        npix[x, y] = lut[pix[x, y]]
            frame_nr += 1
        new.save(self.data_dir + "unblacked.png")
        self.img = new.copy()
        self.pixels = self.img.load()
        self.result_captcha = ""

    def get_bg(self):
        stat = {}
        cstat = {}
        img = self.img.convert("P")
        for bgpath in glob.glob(self.data_dir + "bg/*.gif"):
            stat[bgpath] = 0
            bg = Image.open(bgpath)

            bglut = bg.resize((256, 1))
            bglut.putdata(list(range(256)))
            bglut = list(bglut.convert("RGB").getdata())

            lut = img.resize((256, 1))
            lut.putdata(list(range(256)))
            lut = list(lut.convert("RGB").getdata())

            bgpix = bg.load()
            pix = img.load()
            for x in range(bg.size[0]):
                for y in range(bg.size[1]):
                    rgb_bg = bglut[bgpix[x, y]]
                    rgb_c = lut[pix[x, y]]
                    try:
                        cstat[rgb_c] += 1

                    except Exception:
                        cstat[rgb_c] = 1

                    if rgb_bg == rgb_c:
                        stat[bgpath] += 1
        max_p = 0
        bg = ""
        for bgpath, value in stat.items():
            if max_p < value:
                bg = bgpath
                max_p = value
        return bg

    def substract_bg(self, bgpath):
        bg = Image.open(bgpath)
        img = self.img.convert("P")

        bglut = bg.resize((256, 1))
        bglut.putdata(list(range(256)))
        bglut = list(bglut.convert("RGB").getdata())

        lut = img.resize((256, 1))
        lut.putdata(list(range(256)))
        lut = list(lut.convert("RGB").getdata())

        bgpix = bg.load()
        pix = img.load()
        orgpix = self.img.load()
        for x in range(bg.size[0]):
            for y in range(bg.size[1]):
                rgb_bg = bglut[bgpix[x, y]]
                rgb_c = lut[pix[x, y]]
                if rgb_c == rgb_bg:
                    orgpix[x, y] = (255, 255, 255)

    def eval_black_white(self):
        new = Image.new("RGB", (140, 75))
        pix = new.load()
        orgpix = self.img.load()
        thresh = 4
        for x in range(new.size[0]):
            for y in range(new.size[1]):
                rgb = orgpix[x, y]
                r, g, b = rgb
                pix[x, y] = (255, 255, 255)
                if r > max(b, g) + thresh:
                    pix[x, y] = (0, 0, 0)
                if g < min(r, b):
                    pix[x, y] = (0, 0, 0)
                if g > max(r, b) + thresh:
                    pix[x, y] = (0, 0, 0)
                if b > max(r, g) + thresh:
                    pix[x, y] = (0, 0, 0)
        self.img = new
        self.pixels = self.img.load()

    def recognize(self, image):
        self.load_image(image)
        bg = self.get_bg()
        self.substract_bg(bg)
        self.eval_black_white()
        self.to_greyscale()
        self.img.save(self.data_dir + "cleaned_pass1.png")
        self.clean(4)
        self.clean(4)
        self.img.save(self.data_dir + "cleaned_pass2.png")
        letters = self.split_captcha_letters()
        final = ""
        for n, letter in enumerate(letters):
            self.img = letter
            self.img.save(self.data_dir + "letter{}.png".format(n))
            self.run_tesser(True, True, False, False)
            final += self.result_captcha

        return final
