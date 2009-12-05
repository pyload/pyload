from captcha import OCR
import Image

class LinksaveIn(OCR):
    def __init__(self):
        OCR.__init__(self)
    
    def load_image(self, image):
        im = Image.open(image)
        frame_nr = 0

        lut = im.resize((256, 1))
        lut.putdata(range(256))
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
                    if lut[pix[x, y]] != (0,0,0):
                        npix[x, y] = lut[pix[x, y]]
            frame_nr += 1
        self.image = new.copy()
        self.pixels = self.image.load()
        self.result_captcha = ''

    def get_captcha(self, image):
        self.load_image(image)
        self.run_tesser()

        return self.result_captcha

if __name__ == '__main__':
    import urllib
    ocr = LinksaveIn()
    testurl = "http://linksave.in/captcha/cap.php?hsh=2229185&code=ZzHdhl3UffV3lXTH5U4b7nShXj%2Bwma1vyoNBcbc6lcc%3D"
    urllib.urlretrieve(testurl, "captcha.gif")

    print ocr.get_captcha('captcha.gif')
