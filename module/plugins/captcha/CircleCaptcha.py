# -*- coding: utf-8 -*-
#
#@TODO: Recheck all

from __future__ import division

################################################
class pyload(object):
    def __init__(self):
        self.debug = True

class OCR(object):
    def __init__(self):
        self.pyload = pyload()

    def log_info(self, *args, **kwargs):
        msg = u" | ".join(str(a).strip() for a in args if a)
        print msg

    def log_debug(self, *args, **kwargs):
        msg = u" | ".join(str(a).strip() for a in args if a)
        print msg
################################################

from PIL import Image
from PIL import ImageDraw
import cStringIO
import math
import operator
import urllib

# from module.plugins.internal.OCR import OCR


class ImageSequence:

    def __init__(self, img):
        self.img = img

    def __getitem__(self, ix):
        try:
            if ix:
                self.img.seek(ix)
            return self.img
        except EOFError:
            raise IndexError # end of sequence


class CircleCaptcha(OCR):
    __name__    = "CircleCaptcha"
    __type__    = "ocr"
    __version__ = "1.08"
    __status__  = "testing"

    __description__ = """Circle captcha ocr plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Sasch", "gsasch@gmail.com")]


    _DEBUG = False
    points_of_circle_found = []

    BACKGROUND = 250
    BLACKCOLOR = 5


    def clean_image(self, im, pix):
        clean_depth = 1

        image_height = xrange(1, int(im.size[1]))
        image_width = xrange(1, int(im.size[0]))
        how_many = 0
        cur_color = self.BACKGROUND

        for _y in image_height:
            # jump = True
            how_many = 0
            for _x in image_width:
                cur_pix = pix[_x, _y]

                if cur_pix > self.BACKGROUND:
                    if how_many <= clean_depth and how_many > 0:
                        #: Clean pixel
                        for ic in xrange(1, clean_depth+1):
                            if _x -ic > 0:
                                pix[_x-ic, _y] = self.BACKGROUND
                    how_many = 0
                    cur_color = cur_pix
                    # jump = False
                    # self.log_debug(x, y, jump, 2)
                else:
                    if how_many == 0:
                        #: Found pixel
                        how_many += 1
                        cur_color = cur_pix
                        # jump = True
                        # self.log_debug(x, y, jump, 2)
                    else:
                        how_many += 1
            if how_many == 1:
                #: Clean pixel
                pix[_x-1, _y] = self.BACKGROUND

        cur_color = self.BACKGROUND
        for _x in image_width:
            # jump = True
            how_many = 0
            for _y in image_height:
                cur_pix = pix[_x, _y]
                # if jump is True:
                if cur_pix > self.BACKGROUND:
                    if how_many <= clean_depth and how_many > 0:
                        #: Clean pixel
                        for ic in xrange(1, clean_depth+1):
                            #: raw_input('2'+str(ic))
                            if _y-ic > 0:
                                pix[_x, _y-ic] = self.BACKGROUND
                    how_many = 0
                    cur_color = cur_pix
                    # jump = False
                    # self.log_debug(x, y, jump)
                else:
                    if how_many == 0:
                        #: Found pixel
                        how_many += 1
                        cur_color = cur_pix
                        # jump = True
                        # self.log_debug(x, y, True)
                    else:
                        how_many += 1
            if how_many == 1:
                #: Clean pixel
                pix[_x-1, _y] = self.BACKGROUND

        #: return -1


    def find_first_pixel_x(self, im, pix, cur_x, cur_y, color=-1, exit_with_black=False):
        image_height = xrange(1, int(im.size[1]))
        image_width = xrange(cur_x + 1, int(im.size[0]))
        jump = True
        res = (-1, -1)
        black_found = 0
        for _x in image_width:
            cur_pix = pix[_x, cur_y]

            if cur_pix < self.BLACKCOLOR:
                black_found += 1
                if exit_with_black is True and black_found >= 3:
                    break  #: Exit if found black
                else:
                    continue

            if cur_pix >= self.BACKGROUND:
                #: Found first pixel white
                jump = False
                continue

            if (cur_pix < self.BACKGROUND and color == -1) or (cur_pix == color and color > -1):
                if jump is False:
                    #: Found pixel
                    cur_color = cur_pix
                    res = (_x, cur_color)
                    break

        return res


    def find_last_pixel_x(self, im, pix, cur_x, cur_y, color=-1, exit_with_black=False):
        image_height = xrange(1, int(im.size[1]))
        image_width = xrange(cur_x + 1, int(im.size[0]))
        res = (-1, -1)
        black_found = 0
        for x in image_width:
            cur_pix = pix[x, cur_y]

            if cur_pix < self.BLACKCOLOR:
                black_found += 1
                if exit_with_black is True and black_found >= 3:
                    break  #: Exit if found black
                else:
                    continue

            if cur_pix >= self.BACKGROUND:
                if res != (-1, -1):
                    #: Found last pixel and the first white
                    break

            if (cur_pix < self.BACKGROUND and color == -1) or (cur_pix == color and color > -1):
                #: Found pixel
                cur_color = cur_pix
                res = (x, cur_color)

        return res


    def find_last_pixel_y(self, im, pix, cur_x, cur_y, down_to_up, color = -1, exit_with_black = False):
        if down_to_up is False:
            image_height = xrange(int(cur_y) + 1, int(im.size[1]) - 1)
        else:
            image_height = xrange(int(cur_y) - 1, 1, -1)
        res = (-1, -1)
        black_found = 0
        for _y in image_height:
            cur_pix = pix[cur_x, _y]

            if cur_pix < self.BLACKCOLOR:
                black_found += 1
                if exit_with_black is True and black_found >= 3:
                    break  #: Exit if found black
                else:
                    continue

            if cur_pix >= self.BACKGROUND:
                if res != (-1, -1):
                    #: Found last pixel and the first white
                    break

            if (cur_pix < self.BACKGROUND and color == -1) or (cur_pix == color and color > -1):
                #: Found pixel
                cur_color = cur_pix
                res = (_y, color)

        return res


    def find_circle(self, pix, x1, y1, x2, y2, x3, y3):
        #: Trasposizione coordinate
        #: A(0, 0) B(x2-x1, y2-y1) C(x3-x1, y3-y1)
        #: x**2+y**2+ax+bx+c=0
        p1 = (0, 0)
        p2 = (x2-x1, y2-y1)
        p3 = (x3-x1, y3-y1)

        #: 1
        c=0
        #: 2
        #: p2[0]**2+a*p2[0]+c=0
        #: a*p2[0]=-1*(p2[0]**2-c)
        #: a=(-1*(p2[0]**2-c))/p2[0]
        a=(-1*(p2[0]**2-c))/p2[0]
        #: 3
        #: p3[0]**2+p3[1]**2+a*p3[0]+b*p3[1]+c=0
        #: b*p3[1]=-(p3[0]**2+p3[1]**2+a*p3[0]+c)
        #: b=(-1 * (p3[0]**2+p3[1]**2+a*p3[0]+c)) / p3[1]
        b=(-1 * (p3[0]**2+p3[1]**2+a*p3[0]+c)) / p3[1]

        r=math.floor(math.sqrt((-1*(a/2))**2+(-1*(b/2))**2))
        cx=math.floor((-1*(a/2))+x1)
        cy=math.floor((-1*(b/2))+y1)

        return cx, cy, r


    def verify_circle_new(self, im, pix, c):
        """
            This is the MAIN function to recognize the circle
            returns:
                1 -> Found closed circle
                0 -> Found open circle
                -1 -> Not found circle
                -2 -> Found black position then leave position
        """
        image_height = xrange(int(c[1]-c[2]), int(c[1]+c[2]))
        image_width = xrange(int(c[0]-c[2]), int(c[0]+c[2]))

        min_ray = 15
        max_ray = 30
        exact_find = False

        how_many = 0
        missing = 0
        missing_consecutive = 0
        missing_list = []

        min_x = max_x = min_y = max_y = 0

        points_of_circle = []

        if (c[2] < min_ray) or (c[2] > max_ray):
            return -1

        #: Check cardinal points (at least 3) (if found i have to leave this position)
        if pix[c[0] + c[2], c[1]] < self.BLACKCOLOR:
            return -2
        if pix[c[0] - c[2], c[1]] < self.BLACKCOLOR:
            return -2
        if pix[c[0], c[1] + c[2]] < self.BLACKCOLOR:
            return -2
        if pix[c[0], c[1] - c[2]] < self.BLACKCOLOR:
            return -2

        cardinal_points = 0
        if self.verify_point(im, pix, c[0] + c[2], c[1], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0] + c[2], c[1], False) == -1:
            return -2
        if self.verify_point(im, pix, c[0] - c[2], c[1], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0] - c[2], c[1], False) == -1:
            return -2
        if self.verify_point(im, pix, c[0], c[1] + c[2], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0], c[1] + c[2], False) == -1:
            return -2
        if self.verify_point(im, pix, c[0], c[1] - c[2], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0], c[1] - c[2], False) == -1:
            return -2
        if cardinal_points < 3:
            return -1

        for x in image_width:
            #: Pitagora
            y = int(round(c[1]- math.sqrt(c[2]**2-(c[0]-x)**2)))
            y2= int(round(c[1]+ math.sqrt(c[2]**2-(c[0]-x)**2)))

            how_many += 2
            if self.verify_point(im, pix, x, y, exact_find) == 0:
                missing += 1
                missing_list.append((x, y))
            else:
                points_of_circle.append((x, y))

            if self.verify_point(im, pix, x, y, False) == -1:
                return -2

            if self.verify_point(im, pix, x, y2, exact_find) == 0:
                missing += 1
                missing_list.append((x, y2))
            else:
                points_of_circle.append((x, y2))

            if self.verify_point(im, pix, x, y2, False) == -1:
                return -2


    def verify_circle(self, im, pix, c):
        """
            This is the MAIN function to recognize the circle
            returns:
                1 -> Found closed circle
                0 -> Found open circle
                -1 -> Not found circle
                -2 -> Found black position then leave position
        """
        image_height = xrange(int(c[1]-c[2]), int(c[1]+c[2]))
        image_width = xrange(int(c[0]-c[2]), int(c[0]+c[2]))

        min_ray = 15
        max_ray = 30
        exact_find = False

        how_many = 0
        missing = 0
        missing_consecutive = 0
        missing_list = []

        min_x = max_x = min_y = max_y = 0

        points_of_circle = []

        if (c[2] < min_ray) or (c[2] > max_ray):
            return -1

        #: Check cardinal points (at least 3) (if found i have to leave this position)
        if pix[c[0] + c[2], c[1]] < self.BLACKCOLOR:
            return -2
        if pix[c[0] - c[2], c[1]] < self.BLACKCOLOR:
            return -2
        if pix[c[0], c[1] + c[2]] < self.BLACKCOLOR:
            return -2
        if pix[c[0], c[1] - c[2]] < self.BLACKCOLOR:
            return -2

        cardinal_points = 0
        if self.verify_point(im, pix, c[0] + c[2], c[1], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0] + c[2], c[1], False) == -1:
            return -2
        if self.verify_point(im, pix, c[0] - c[2], c[1], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0] - c[2], c[1], False) == -1:
            return -2
        if self.verify_point(im, pix, c[0], c[1] + c[2], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0], c[1] + c[2], False) == -1:
            return -2
        if self.verify_point(im, pix, c[0], c[1] - c[2], True) == 1:
            cardinal_points += 1
        if self.verify_point(im, pix, c[0], c[1] - c[2], False) == -1:
            return -2
        if cardinal_points < 3:
            return -1

        for x in image_width:
            #: Pitagora
            _y = int(round(c[1]- math.sqrt(c[2]**2-(c[0]-x)**2)))
            y2= int(round(c[1]+ math.sqrt(c[2]**2-(c[0]-x)**2)))

            how_many += 2
            if self.verify_point(im, pix, x, _y, exact_find) == 0:
                missing += 1
                missing_list.append((x, _y))
            else:
                points_of_circle.append((x, _y))

            if self.verify_point(im, pix, x, _y, False) == -1:
                return -2

            if self.verify_point(im, pix, x, y2, exact_find) == 0:
                missing += 1
                missing_list.append((x, y2))
            else:
                points_of_circle.append((x, y2))

            if self.verify_point(im, pix, x, y2, False) == -1:
                return -2

        for _y in image_height:
            #: Pitagora
            x = int(round(c[0]- math.sqrt(c[2]**2-(c[1]-_y)**2)))
            x2= int(round(c[0]+ math.sqrt(c[2]**2-(c[1]-_y)**2)))

            how_many += 2
            if self.verify_point(im, pix, x, _y, exact_find) == 0:
                missing += 1
                missing_list.append((x, _y))
            else:
                points_of_circle.append((x, _y))

            if self.verify_point(im, pix, x, _y, False) == -1:
                return -2

            if self.verify_point(im, pix, x2, _y, exact_find) == 0:
                missing += 1
                missing_list.append((x2, _y))
            else:
                points_of_circle.append((x2, _y))

            if self.verify_point(im, pix, x2, _y, exact_find) == -1:
                return -2

        for _p in missing_list:
                #: Left and bottom
            if (self.verify_point(im, pix, _p[0]-1, _p[1], exact_find) == 1
                and self.verify_point(im, pix, _p[0], _p[1]+1, exact_find) == 1):
                missing -= 1
            elif (self.verify_point(im, pix, _p[0]-1, _p[1], exact_find) == 1
                  and self.verify_point(im, pix, _p[0], _p[1]-1, exact_find) == 1):
                missing -= 1
                #: Right and bottom
            elif (self.verify_point(im, pix, _p[0]+1, _p[1], exact_find) == 1
                  and self.verify_point(im, pix, _p[0], _p[1]+1, exact_find) == 1):
                missing -= 1
                #: Right and up
            elif (self.verify_point(im, pix, _p[0]+1, _p[1], exact_find) == 1
                  and self.verify_point(im, pix, _p[0], _p[1]-1, exact_find) == 1):
                missing -= 1

            if ((_p[0], _p[1]+1) in missing_list
                or (_p[0], _p[1]-1) in missing_list
                or (_p[0]+1, _p[1]) in missing_list
                or (_p[0]-1, _p[1]) in missing_list
                or (_p[0]+1, _p[1]+1) in missing_list
                or (_p[0]-1, _p[1]+1) in missing_list
                or (_p[0]+1, _p[1]-1) in missing_list
                or (_p[0]-1, _p[1]-1) in missing_list
                or self.verify_point(im, pix, _p[0], _p[1], False) == 1):
                missing_consecutive += 1
            # else:
            #     pix[p[0], p[1]] = 0

        if missing / how_many > 0:
            indice = c[2] * (missing / how_many)
        else:
            indice = 0

        if len(missing_list) > 0:
            min_x = min(missing_list, key=operator.itemgetter(0))[0]
            max_x = max(missing_list, key=operator.itemgetter(0))[0]

            min_y = min(missing_list, key=operator.itemgetter(1))[1]
            max_y = max(missing_list, key=operator.itemgetter(1))[1]

        #: Assial Simmetric
        self.log_debug("Center: %s,%s"                  % (c[0], c[1]))
        self.log_debug("Missing: %s"                    % missing)
        self.log_debug("Howmany: %s"                    % how_many)
        self.log_debug("Ratio: %s"                      % (missing / how_many))
        self.log_debug("Missing consecutives: %s"       % missing_consecutive)
        self.log_debug("Missing X length: %s:%s"        % (min_x, max_x))
        self.log_debug("Missing Y length: %s:%s"        % (min_y, max_y))
        self.log_debug("Ratio without consecutives: %s" % ((missing - missing_consecutive) / how_many))
        self.log_debug("List missing: %s"               % missing_list)

        #: Length of missing cannot be over 75% of diameter

        if max_x - min_x >= c[2] * 2 * 0.75:
            return -1
        if max_y - min_y >= c[2] * 2 * 0.75:
            #: raw_input('tro')
            return -1
        """
        #: length of missing cannot be less 10% of diameter
        if max_x - min_x < c[2] * 2 * 0.10 and max_y - min_y < c[2] * 2 * 0.10:
            return -1
        """
        if missing / how_many > 0.25 or \
            missing_consecutive >= (how_many / 4) * 2 or \
            how_many < 80:
            return -1
        # elif missing / how_many < 0.10:
        elif missing == 0:
            self.points_of_circle_found.extend(points_of_circle)
            return 1
        elif (missing - missing_consecutive) / how_many < 0.20:
            return 0
        else:
            self.points_of_circle_found.extend(points_of_circle)
            return 1


    def verify_point(self, im, pix, x, y, exact, color = -1):
        #: Verify point
        result = 0

        if x < 0 or x >= im.size[0]:
            return result
        if y < 0 or y >= im.size[1]:
            return result

        cur_pix = pix[x, y]
        if (cur_pix == color and color > -1) or (cur_pix < self.BACKGROUND and color == -1):
            if cur_pix > self.BLACKCOLOR:
                result = 1
            else:
                result = -1

        #: Verify around
        if exact is False:
            if x + 1 < im.size[0]:
                cur_pix = pix[x+1, y]
                if (cur_pix == color and color > -1) or (cur_pix < self.BACKGROUND and color == -1):
                    if cur_pix > self.BLACKCOLOR:
                        result = 1
                if cur_pix <= self.BLACKCOLOR:
                    result = -1

            if x > 0:
                cur_pix = pix[x-1, y]
                if (cur_pix == color and color > -1) or (cur_pix < self.BACKGROUND and color == -1):
                    if cur_pix > self.BLACKCOLOR:
                        result = 1
                if cur_pix <= self.BLACKCOLOR:
                    result = -1
        # self.log_debug(str((x, y)) + " = " + str(result))
        return result


    def recognize(self, image):
        iDebugSaveFile = 0
        my_palette = None
        for _img in ImageSequence(image):
            _img.save("orig.png", "png")
            if my_palette is not None:
                _img.putpalette(my_palette)
            my_palette = _img.getpalette()
            _img = _img.convert('L')

            if self.pyload.debug:
                iDebugSaveFile += 1
                # if iDebugSaveFile < 7:
                    # continue
                _img.save("output" + str(iDebugSaveFile) + ".png", "png")
                raw_input('frame: '+ str(_img))

            pix = _img.load()

            stepheight = xrange(1, _img.size[1], 2)
            #: stepheight = xrange(45, 47)
            imagewidth = xrange(1, _img.size[0])
            lstPoints = [] # Declares an empty list for the points
            lstX = [] # CoordinateX
            lstY = [] # CoordinateY
            lstColors = [] # Declares an empty list named lst
            min_distance = 10
            max_diameter = 70

            if self.pyload.debug:
                img_debug = _img.copy()
                draw = ImageDraw.Draw(img_debug)
                pix_debug = img_debug.load()

            #: Clean image for powerfull search
            self.clean_image(_img, pix)
            _img.save("cleaned" + str(iDebugSaveFile) + ".png", "png")

            circles_found = set()
            findnewcircle = True

            #: Finding all the circles
            for y1 in stepheight:
                x1 = 1
                curcolor = -1
                for k in xrange(1, 100):
                    findnewcircle = False
                    retval = self.find_first_pixel_x(_img, pix, x1, y1, -1, False)
                    x1 = retval[0]
                    curcolor = retval[1]
                    if x1 == -2:
                        break
                    if x1 == -1:
                        break
                    if self.pyload.debug:
                        self.log_debug("x1, y1 -> " + str((x1, y1)) + ": " + str(pix[x1, y1]))

                    if (x1, y1) in self.points_of_circle_found:
                        if self.pyload.debug:
                            self.log_debug("Found " + str((x1, y1)))
                        continue

                    if self.pyload.debug:
                        pix_debug[x1, y1] = 45 #(255, 0, 0, 255)
                    #: circles_found 1 pixel, seeking x2, y2
                    x2 = x1
                    y2 = y1
                    for i in xrange(1, 100):
                        retval = self.find_last_pixel_x(_img, pix, x2, y2, -1, True)
                        x2 = retval[0]
                        if x1 == -2:
                            findnewcircle = True
                            break
                        if x2 == -1:
                            break
                        if self.pyload.debug:
                            self.log_debug("x2, y2 -> " + str((x2, y1)) + ": " + str(pix[x2, y1]))
                        if abs(x2 - x1) < min_distance:
                            continue
                        if abs(x2 - x1) > (_img.size[1] * 2 / 3):
                            break
                        if abs(x2 - x1) > max_diameter:
                            break

                        if self.pyload.debug:
                            pix_debug[x2, y2] = 65 #(0, 255, 0, 255)
                        #: circles_found 2 pixel, seeking x3, y3
                        #: Verify cord

                        for invert in xrange(0, 2):
                            x3 = math.floor(x2 - ((x2 - x1) / 2))
                            y3 = y1
                            for j in xrange(1, 50):
                                retval = self.find_last_pixel_y(_img, pix, x3, y3, True if invert == 1 else False, -1, True)
                                # self.log_debug(x3, y3, retval[0], invert)
                                y3 = retval[0]
                                if y3 == -2:
                                    findnewcircle = True
                                    break
                                if y3 == -1:
                                    break

                                if self.pyload.debug:
                                    self.log_debug("x3, y3 -> " + str((x3, y3)) + ": " + str(pix[x3, y3]))
                                #: Verify cord
                                if abs(y3 - y2) < min_distance:
                                    continue
                                if abs(y3 - y2) > (_img.size[1] * 2 / 3):
                                    break
                                if abs(y3 - y2) > max_diameter:
                                    break

                                if self.pyload.debug:
                                    pix_debug[x3, y3] = 85
                                #: circles_found 3 pixel. try circle
                                circle = self.find_circle(pix, x1, y1, x2, y2, x3, y3)

                                if circle[0] + circle[2] >= _img.size[0] or circle[1] + circle[2] >= _img.size[1] or circle[0] - circle[2] <= 0 or circle[1] - circle[2] <= 0:
                                    continue

                                if self.pyload.debug:
                                    pix_debug[circle[0], circle[1]] = 0
                                #: (x-r, y-r, x+r, y+r)
                                verified = self.verify_circle(_img, pix, circle)

                                if verified == -1:
                                    verified = -1
                                elif verified == 0:
                                    circles_found.add(((circle[0], circle[1], circle[2]), verified))
                                    findnewcircle = True
                                elif verified == 1:
                                    circles_found.add(((circle[0], circle[1], circle[2]), verified))
                                    findnewcircle = True

                                if self.pyload.debug:
                                    _pause = ""
                                    # if verified == -1:
                                        # draw.ellipse((circle[0]-circle[2], circle[1]-circle[2], circle[0]+circle[2], circle[1]+circle[2]), outline=0)
                                        # _pause = "NOTDOUND"
                                        # img_debug.save("debug.png", "png")
                                    if verified == 0:
                                        draw.ellipse((circle[0]-circle[2], circle[1]-circle[2], circle[0]+circle[2], circle[1]+circle[2]), outline=120, fill=128)
                                        _pause = "OPENED"

                                    if verified == 1:
                                        draw.ellipse((circle[0]-circle[2], circle[1]-circle[2], circle[0]+circle[2], circle[1]+circle[2]), outline=65, fill=128)
                                        _pause = "CLOSED"

                                    img_debug.save("debug" + str(iDebugSaveFile) +".png", "png")
                                    iDebugSaveFile += 1

                                    # if _pause != "":
                                    #     valore = raw_input('Found ' + _pause + ' CIRCLE circle press [Enter] = continue / [q] for Quit: ' + str(verified))
                                    #     if valore == "q":
                                    #         sys.exit()

                                if findnewcircle is True:
                                    break
                            if findnewcircle is True:
                                break
                        if findnewcircle is True:
                            break

            if self.pyload.debug:
                self.log_debug("Howmany opened circle?", circles_found)

            #: Clean results
            for circle in circles_found:
                verify = circle[1]
                if verify == 0:
                    p = circle[0]
                    if (((p[0], p[1]+1, p[2]), 1) in circles_found
                        or ((p[0], p[1]-1, p[2]), 1) in circles_found
                        or ((p[0]+1, p[1], p[2]), 1) in circles_found
                        or ((p[0]-1, p[1], p[2]), 1) in circles_found
                        or ((p[0]+1, p[1]+1, p[2]), 1) in circles_found
                        or ((p[0]-1, p[1]+1, p[2]), 1) in circles_found
                        or ((p[0]+1, p[1]-1, p[2]), 1) in circles_found
                        or ((p[0]-1, p[1]-1, p[2]), 1) in circles_found):

                        #: Delete nearly circle
                        verify = -1

                    if (((p[0], p[1]+1, p[2]+1), 1) in circles_found
                        or ((p[0], p[1]-1, p[2]+1), 1) in circles_found
                        or ((p[0]+1, p[1], p[2]+1), 1) in circles_found
                        or ((p[0]-1, p[1], p[2]+1), 1) in circles_found
                        or ((p[0]+1, p[1]+1, p[2]+1), 1) in circles_found
                        or ((p[0]-1, p[1]+1, p[2]+1), 1) in circles_found
                        or ((p[0]+1, p[1]-1, p[2]+1), 1) in circles_found
                        or ((p[0]-1, p[1]-1, p[2]+1), 1) in circles_found):

                        #: Delete nearly circle
                        verify = -1

                    if (((p[0], p[1]+1, p[2]-1), 1) in circles_found
                        or ((p[0], p[1]-1, p[2]-1), 1) in circles_found
                        or ((p[0]+1, p[1], p[2]-1), 1) in circles_found
                        or ((p[0]-1, p[1], p[2]-1), 1) in circles_found
                        or ((p[0]+1, p[1]+1, p[2]-1), 1) in circles_found
                        or ((p[0]-1, p[1]+1, p[2]-1), 1) in circles_found
                        or ((p[0]+1, p[1]-1, p[2]-1), 1) in circles_found
                        or ((p[0]-1, p[1]-1, p[2]-1), 1) in circles_found):

                        #: Delete nearly circle
                        verify = -1

                if verify == 0:
                    if self.pyload.debug:
                        pix[circle[0][0], circle[0][1]] = 90 #(255, 255, 0)
                        _img.save("output.png", "png")
                        return circle[0][0], circle[0][1]

                elif verify == 1:
                    if self.pyload.debug:
                        pix[circle[0][0], circle[0][1]] = 40 #(255, 0, 0)
                        _img.save("output.png", "png")

                else:
                    if self.pyload.debug:
                        pix[circle[0][0], circle[0][1]] = 180 #(0, 0, 255)
                        _img.save("output.png", "png")

        if self.pyload.debug:
            _img.save("output.png", "png")


    #: Return coordinates of opened circle (eg (x, y))
    def decrypt_from_web(self, url):
        file = cStringIO.StringIO(urllib.urlopen(url).read())
        img = Image.open(file)
        coords = self.recognize(img)
        self.log_info(_("Coords: %s") % repr(coords))


    #: Return coordinates of opened circle (eg (x, y))
    def decrypt_from_file(self, filename):
        coords = self.recognize(Image.open(filename))  #: Can be many different formats.
        self.log_info(_("Coords: %s") % repr(coords))


##DEBUG
_ = lambda x: x
import datetime
a = datetime.datetime.now()
x = CircleCaptcha()
# coords = x.decrypt_from_file("c:\Home\Programming\Projects\pyLoad\dummy\CircleCaptcha\circlecaptcha.png")
coords = x.decrypt_from_web("http://ncrypt.in/classes/captcha/circlecaptcha.php")
b = datetime.datetime.now()
print ("Elapsed time: %s seconds" % (b-a).seconds)
