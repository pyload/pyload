import Image
import ImageOps
import subprocess

class OCR(object):
    def __init__(self):
        pass

    def load_image(self, image):
        self.image = Image.open(image)
        self.pixels = self.image.load()
        self.image_name = 'captcha_clean.png'
        self.result_captcha = ''

    def unload():
        """delete all tmp images"""
        pass

    def threshold(self, value):
        self.image = self.image.point(lambda a: a * value +10)

    def run_gocr(self):
        self.image.save(self.image_name)
        cmd = ['gocr', self.image_name]
        self.result_captcha = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].replace('\n','')

    def run_tesser(self):
        self.image.save('captcha.tif', 'TIFF')
        cmd = ['tesseract', 'captcha.tif', '0']
        self.result_captcha = subprocess.Popen(cmd)
        self.result_captcha.wait()
        cmd = ['cat', '0.txt']
        self.result_captcha = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].replace('\n','')

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
           # no point in processing white pixels since we only want to remove black pixels
                if pixels[x, y] == 255: continue

                count = 0

                try:
                    if pixels[x-1, y-1] != 255: count += 1
                    if pixels[x-1, y  ] != 255: count += 1
                    if pixels[x-1, y+1] != 255: count += 1
                    if pixels[x, y+1  ] != 255: count += 1
                    if pixels[x+1, y+1] != 255: count += 1
                    if pixels[x+1, y  ] != 255: count += 1
                    if pixels[x+1, y-1] != 255: count += 1
                    if pixels[x, y-1  ] != 255: count += 1
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
