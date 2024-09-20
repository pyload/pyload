# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: Gummibaer
"""
from __future__ import with_statement

from thread import start_new_thread
import sys
import Image
import os
from module.plugins.Hook import Hook


class LinkCryptWsCaptchaSolver(Hook):
    __name__ = "LinkCryptWsCaptchaSolver"
    __version__ = "0.01"
    __description__ = """Solved Captchas"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("timeout", "int", "Timeout (max. 60)", "20"),
                  ("force", "bool", "Force CT even if client is connected", True), ]
    __author_name__ = ("Gummibaer")
    __author_mail__ = ("Gummibaer@wiki-bierkiste.de")

    def checkstyle(self):
        noblack = 0;
        maxy = self.im.size[1]
        maxx = self.im.size[0]
        rgb_im = self.im.convert('RGB')
        pix = rgb_im.load()
        if pix[4, 4][0] == 0 and pix[4, 246][0] == 0  and pix[124, 4][0] == 0  and pix[124, 246][0] == 0:
            self.logDebug("LinkCryptWs Captcha Left Right")
            self.makeleftright()
        if pix[28, 4][0] == 0 and pix[218, 246][0] == 0  and pix[252, 4][0] == 0  and pix[440, 246][0] == 0:
            self.logDebug("LinkCryptWs Captcha Up Down")
            self.makeupdown()
        if pix[10, 50][0] == 0 and pix[160, 50][0] == 0  and pix[10, 200][0] == 0  and pix[160, 200][0] == 0:
            self.logDebug("LinkCryptWs Captcha Caro")
            self.makecaro()
        
    def makeupdown(self):  
        palette = self.im.getpalette()
        nframes = 0
        while self.im:
            if nframes == 7:
                break;
            nframes += 1
            try:
                self.im.seek( nframes )
            except EOFError:
                break;
        self.im.putpalette(palette)
        first = Image.new("RGBA", self.im.size)
        first.paste(self.im)
        while self.im:
            if nframes == 16:
                break;
            nframes += 1
            try:
                self.im.seek( nframes )
            except EOFError:
                break;
        self.im.putpalette(palette)
        second = Image.new("RGBA", self.im.size)
        second.paste(self.im)
        [x,y]=first.size
        leftpart_top = (0, 0, x/2, y)
        part = second.crop(leftpart_top)
        result = first.copy()
        result.paste(part, leftpart_top)
        result.convert("RGBA")
        pix = result.load()
        whitePixel = (255, 255, 255)
        for y in xrange(18):
            for x in xrange(470):
                pix[x, y] = whitePixel
        self.im = result

    def makecaro(self):  
        palette = self.im.getpalette()
        nframes = 0
        self.im.putpalette(palette)
        first = Image.new("RGBA", self.im.size)
        first.paste(self.im)
        while self.im:
            if nframes == 15:
                break;
            nframes += 1
            try:
                self.im.seek( nframes )
            except EOFError:
                break;
        self.im.putpalette(palette)
        second = Image.new("RGBA", self.im.size)
        second.paste(self.im)
        [x,y]=first.size
        leftpart_top = (0, 0, 200, y)
        part = second.crop(leftpart_top)
        result = first.copy()
        result.paste(part, leftpart_top)
        self.im = result

    def makeleftright(self):  
        palette = self.im.getpalette()
        nframes = 0
        self.im.putpalette(palette)
        first = Image.new("RGBA", self.im.size)
        first.paste(self.im)
        while self.im:
            if nframes == 20:
                break;
            nframes += 1
            try:
                self.im.seek( nframes )
            except EOFError:
                break;
        self.im.putpalette(palette)
        second = Image.new("RGBA", self.im.size)
        second.paste(self.im)
        [x,y]=first.size
        leftpart_top = (0, 0, x/2, y)
        part = second.crop(leftpart_top)
        result = first.copy()
        result.paste(part, leftpart_top)
        self.im = result


    def searchopencycle(self):
        gray = self.im.convert('L')
        self.im = gray.point(lambda x: 0 if x<220 else 255, '1')
        self.im = self.im.convert('RGB')
        blackPixel = (0, 0, 0)
        whitePixel = (255, 255, 255)
        colorPixel = (255, 0, 0)
        pix = self.im.load()
        [xsize,ysize]=self.im.size
        for y in xrange(ysize):
            for x in xrange(xsize):
                if pix[x, y] != whitePixel:
                    if y <= 245:
                        if pix[x, y+1] == blackPixel and pix[x, y+2] == blackPixel and pix[x, y+3] == blackPixel:
                            checkblack = "true"
                            for z in xrange(y,y+3):
                                for i in xrange(x,x+8):
                                    if checkblack == "true" and pix[i, z] != blackPixel:
                                        checkblack = "false"
                            if checkblack == "true": 
                                pix[x, y] = colorPixel
                                pix[x+5, y+20] = colorPixel
                                self.logDebug("LinkCryptWs Result first Check %dx%d" %(x, y))
                                return (x, y)
                                #return (x+10, y+20)
                            if x+40 <= xsize:
                                x = x + 40
        self.im.rotate(180).show()
        pix = self.im.load()
        for y in xrange(ysize):
            for x in xrange(xsize):
                if pix[x, y] != whitePixel:
                    if y <= 245:
                        if pix[x, y+1] == blackPixel and pix[x, y+2] == blackPixel and pix[x, y+3] == blackPixel:
                            checkblack = "true"
                            for z in xrange(y,y+3):
                                for i in xrange(x,x+8):
                                    if checkblack == "true" and pix[i, z] != blackPixel:
                                        checkblack = "false"
                            if checkblack == "true": 
                                pix[x, y] = colorPixel
                                pix[x+5, y+20] = colorPixel
                                self.logDebug("LinkCryptWs Result second Check %dx%d" %(x, y))
                                return (x, y)
                                #return (x+10, y+20)
                            if x+40 <= xsize:
                                x = x + 40
        self.logDebug("LinkCryptWs Result Fail")
        return (0,0)
    def load_image(self, image):
        self.logDebug("load_image")
        self.im = Image.open(image)
        self.logDebug("checkstyle")
        self.checkstyle()
        self.logDebug("checkstyle finisched")
        return self.searchopencycle()

    def newCaptchaTask(self, task):
        if not task.isPositional():
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False
            
        if "tmpCaptcha_LinkCryptWs" in task.captchaFile:
            self.logDebug("LinkCryptWs newCaptchaTask")
            self.logDebug("LinkCryptWs File %s" % task.captchaFile)
            task.handler.append(self)
            task.setWaiting(self.getConfig("timeout"))
            res = self.load_image(task.captchaFile)
            result = str(res[0]) + ',' + str(res[1])
            self.logInfo("LinkCryptWs Result Finished %s" % result)
            task.setResult(result)
        else:
             return False
    def captchaCorrect(self, task):
        self.logInfo("Captcha was correkt.")

    def captchaInvalid(self, task):
        self.logError("Captcha was not correkt.")
