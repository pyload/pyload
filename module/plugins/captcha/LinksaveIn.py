# -*- coding: utf-8 -*-

try:
    from PIL import Image

except ImportError:
    import Image

import glob
import os

from module.plugins.internal.OCR import OCR


class LinksaveIn(OCR):
    __name__    = "LinksaveIn"
    __type__    = "ocr"
    __version__ = "0.14"
    __status__  = "testing"

    __description__ = """Linksave.in ocr plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    def init(self):
        self.data_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep + "LinksaveIn" + os.sep


    def load_image(self, image):
        im = Image.open(image)
        frame_nr = 0

        lut = im.resize((256, 1))
        lut.putdata(xrange(256))
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
            for x in xrange(frame.size[0]):
                for y in xrange(frame.size[1]):
                    if lut[pix[x, y]] != (0, 0, 0):
                        npix[x, y] = lut[pix[x, y]]
            frame_nr += 1
        new.save(self.data_dir+"unblacked.png")
        self.image = new.copy()
        self.pixels = self.image.load()
        self.result_captcha = ""


    def get_bg(self):
        stat = {}
        cstat = {}
        img = self.image.convert("P")
        for bgpath in glob.glob(self.data_dir+"bg/*.gif"):
            stat[bgpath] = 0
            bg = Image.open(bgpath)

            bglut = bg.resize((256, 1))
            bglut.putdata(xrange(256))
            bglut = list(bglut.convert("RGB").getdata())

            lut = img.resize((256, 1))
            lut.putdata(xrange(256))
            lut = list(lut.convert("RGB").getdata())

            bgpix = bg.load()
            pix = img.load()
            for x in xrange(bg.size[0]):
                for y in xrange(bg.size[1]):
                    rgb_bg = bglut[bgpix[x, y]]
                    rgb_c = lut[pix[x, y]]
                    try:
                        cstat[rgb_c] += 1
                    except Exception:
                        cstat[rgb_c] = 1
                    if rgb_bg is rgb_c:
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
        img = self.image.convert("P")

        bglut = bg.resize((256, 1))
        bglut.putdata(xrange(256))
        bglut = list(bglut.convert("RGB").getdata())

        lut = img.resize((256, 1))
        lut.putdata(xrange(256))
        lut = list(lut.convert("RGB").getdata())

        bgpix = bg.load()
        pix = img.load()
        orgpix = self.image.load()
        for x in xrange(bg.size[0]):
            for y in xrange(bg.size[1]):
                rgb_bg = bglut[bgpix[x, y]]
                rgb_c = lut[pix[x, y]]
                if rgb_c is rgb_bg:
                    orgpix[x, y] = (255, 255, 255)


    def eval_black_white(self):
        new = Image.new("RGB", (140, 75))
        pix = new.load()
        orgpix = self.image.load()
        thresh = 4
        for x in xrange(new.size[0]):
            for y in xrange(new.size[1]):
                rgb = orgpix[x, y]
                r, g, b = rgb
                pix[x, y] = (255, 255, 255)
                if r > max(b, g)+thresh:
                    pix[x, y] = (0, 0, 0)
                if g < min(r, b):
                    pix[x, y] = (0, 0, 0)
                if g > max(r, b)+thresh:
                    pix[x, y] = (0, 0, 0)
                if b > max(r, g)+thresh:
                    pix[x, y] = (0, 0, 0)
        self.image = new
        self.pixels = self.image.load()


    def recognize(self, image):
        self.load_image(image)
        bg = self.get_bg()
        self.substract_bg(bg)
        self.eval_black_white()
        self.to_greyscale()
        self.image.save(self.data_dir+"cleaned_pass1.png")
        self.clean(4)
        self.clean(4)
        self.image.save(self.data_dir+"cleaned_pass2.png")
        letters = self.split_captcha_letters()
        final = ""
        for n, letter in enumerate(letters):
            self.image = letter
            self.image.save(ocr.data_dir+"letter%d.png" % n)
            self.run_tesser(True, True, False, False)
            final += self.result_captcha

        return final
