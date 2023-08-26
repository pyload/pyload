# -*- coding: utf-8 -*-

import io
import json
import os
import re
import urllib.parse

import pycurl
from pyload.core.utils import purge

from ..anticaptchas.HCaptcha import HCaptcha
from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.xfs_downloader import XFSDownloader
from ..helpers import check_module, parse_html_tag_attr_value

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    pass


def _text_size(draw, text, font=None):
    try:
        text_size = draw.textsize(text, font=font)
    except AttributeError:
        text_bbox = draw.textbbox((0,0), text, font=font)
        text_size = (
            text_bbox[2] - text_bbox[0],
            text_bbox[3] - text_bbox[1]
        )
    return text_size


class XCaptcha:
    def __init__(self, pyfile):
        self.pyfile = pyfile
        self.plugin = pyfile.plugin
        self._ = self.plugin._

    def _load_image(self, url):
        img_data = self.plugin.load(
            self.plugin.fixurl(url), ref=self.pyfile.url, decode=False
        )
        s = io.BytesIO()
        s.write(img_data)
        img = Image.open(s)

        return img

    def _prepare_image(self, tiles, tiles_layout, challenge_msg, challenge_image_url):
        if not check_module("PIL"):
            self.plugin.log_error(
                self._("Missing Pillow lib"),
                self._("Please install python's Pillow library"),
            )
            self.plugin.fail(self._("Missing Pillow lib"))

        # assume all tiles are the same size, including challenge image
        challenge_image = self._load_image(challenge_image_url)
        margin = 6
        tile_size = {
            "width": challenge_image.size[0],
            "height": challenge_image.size[1],
        }
        tile_size_with_margin = {
            "width": tile_size["width"] + margin,
            "height": tile_size["height"] + margin,
        }

        tiles_image_size = {
            "width": tile_size_with_margin["width"] * tiles_layout["width"] - margin,
            "height": tile_size_with_margin["height"] * tiles_layout["height"] - margin,
        }
        tiles_image = Image.new(
            "RGB", (tiles_image_size["width"], tiles_image_size["height"]), "white"
        )
        draw = ImageDraw.Draw(tiles_image)

        if os.name == "nt":
            font = ImageFont.truetype("arialbd", 13)
        else:
            font = None

        margin = 3
        for x in range(tiles_layout["width"]):
            for y in range(tiles_layout["height"]):
                tile_number = y * tiles_layout["width"] + x
                tile_index_text = str(tile_number + 1)

                tile_image = self._load_image(tiles[tile_number][0])
                tile_image_pos = {
                    "x": x * tile_size_with_margin["width"],
                    "y": y * tile_size_with_margin["height"],
                }
                tiles_image.paste(
                    tile_image, (tile_image_pos["x"], tile_image_pos["y"])
                )

                text_size = _text_size(draw, tile_index_text)
                tile_index_text_size = {
                    "width": text_size[0],
                    "height": text_size[1],
                }

                tile_index_text_pos = {
                    "x": tile_image_pos["x"]
                    + tile_size["width"]
                    - tile_index_text_size["width"]
                    - margin,
                    "y": tile_image_pos["y"],
                }

                draw.rectangle(
                    [
                        tile_index_text_pos["x"] - margin,
                        tile_index_text_pos["y"],
                        tile_index_text_pos["x"]
                        + tile_index_text_size["width"]
                        + margin,
                        tile_index_text_pos["y"] + tile_index_text_size["height"],
                    ],
                    fill="white",
                )

                draw.text(
                    (tile_index_text_pos["x"], tile_index_text_pos["y"]),
                    tile_index_text,
                    "#000",
                    font=font,
                )

        _sol = 0
        _eol = 1
        # determine maximum width of line
        while True:
            while _text_size(draw, challenge_msg[_sol:_eol], font=font)[
                0
            ] < tiles_image.size[0] and _eol < len(challenge_msg):
                _eol += 1

            # if we've wrapped the text, then adjust the wrap to the last word
            if _eol < len(challenge_msg):
                _eol = challenge_msg.rfind(" ", 0, _eol)
                if _eol > 0:
                    challenge_msg = (
                        challenge_msg[:_eol] + "\n" + challenge_msg[_eol + 1 :]
                    )
                    _sol = _eol + 1

            else:
                break

        challenge_msg = challenge_msg + '\n(Type image numbers like "2,5,8")'

        text_area_height = 0
        challenge_msg_lines = challenge_msg.split("\n")
        for challenge_line in challenge_msg_lines:
            text_area_height += _text_size(draw, challenge_line, font=font)[1]

        margin = 5
        # add some margin on top and bottom of text
        text_area_height += margin * 2

        dst_image_size = {
            "width": tiles_image_size["width"],
            "height": tiles_image_size["height"]
            + tile_size["height"]
            + text_area_height,
        }
        dst_image = Image.new(
            "RGB", (dst_image_size["width"], dst_image_size["height"]), "white"
        )
        draw = ImageDraw.Draw(dst_image)

        dst_image.paste(
            challenge_image, ((dst_image_size["width"] - tile_size["width"]) // 2, 0)
        )

        current_y = tile_size["height"] + margin
        for challenge_line in challenge_msg_lines:
            line_width, line_height = _text_size(draw, challenge_line, font=font)
            draw.text(
                ((dst_image_size["width"] - line_width) // 2, current_y),
                challenge_line,
                fill="black",
                font=font,
            )
            current_y += line_height

        dst_image.paste(tiles_image, (0, tile_size["height"] + text_area_height))

        with io.BytesIO() as s:
            dst_image.save(s, format="PNG")
            dst = s.getvalue()

        return dst

    def challenge(self):
        self.plugin.log_debug("xCaptcha | Challenge xCaptcha")

        xcaptcha_data = self.plugin.load("https://filejoker.net/xcaptcha/api.js")
        tiles = re.findall(r'url: "(.+?)",\s*val: "(.+?)"', xcaptcha_data)
        if len(tiles) == 0:
            self.plugin.log_error(self._("xCaptcha | pics not found"))
            self.plugin.fail(self._("xCaptcha | pics not found"))

        per_row = int(
            re.search(r'var per_row = parseInt\("(\d+)"\);', xcaptcha_data).group(1)
        )
        tiles_layout = {"width": per_row, "height": len(tiles) // per_row}

        try:
            response_prefix = re.search(
                r"text: '([0-9a-f_]+)' \+ answer\.join", xcaptcha_data
            ).group(1)
        except (AttributeError, IndexError):
            self.plugin.log_error(self._("xCaptcha | prefix pattern not found"))
            self.plugin.fail(self._("xCaptcha | prefix pattern  not found"))

        try:
            example_pic = re.search(
                r'var example_pic = \$\(\'<img>\', {\s*src: "(.+?)"', xcaptcha_data
            ).group(1)
        except (AttributeError, IndexError):
            self.plugin.log_error(self._("xCaptcha | example pic pattern not found"))
            self.plugin.fail(self._("xCaptcha | example pic pattern not found"))

        try:
            example_text = re.search(
                r"var example_text = \$\('<p>', {\s*html: '(.+?)'", xcaptcha_data
            ).group(1)
        except (AttributeError, IndexError):
            self.plugin.log_error(self._("xCaptcha | example text pattern not found"))
            self.plugin.fail(self._("xCaptcha | example text pattern not found"))

        img = self._prepare_image(tiles, tiles_layout, example_text, example_pic)
        response = self.plugin.captcha.decrypt_image(img, input_type="png")

        response = sorted(
            purge.uniquify(
                [
                    int(x) - 1
                    for x in response.split(",")
                    if x.strip().isnumeric() and 1 <= int(x) <= len(tiles)
                ]
            )
        )

        response = response_prefix + "-".join([tiles[x][1] for x in response])

        return response


class FilejokerNet(XFSDownloader):
    __name__ = "FilejokerNet"
    __type__ = "downloader"
    __version__ = "0.16"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filejoker\.net/(?:file/)?(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filejoker.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "filejoker.net"

    ERROR_PATTERN = r"Wrong Captcha|Session expired|Your download has not finished yet"
    PREMIUM_ONLY_PATTERN = "Free Members can download files no bigger"

    WAIT_PATTERN =  r'<span id="count" class="alert-success">([\w ]+?)</span>\s*seconds'
    DL_LIMIT_PATTERN = r"Wait [\w ]+? to download for free."
    TEMP_OFFLINE_PATTERN = r"Your download has not finished yet"

    INFO_PATTERN = r'<div class="name-size"><span>(?P<N>.+?)</span> <p>(?:\()?(?P<S>[\d.,]+) (?P<U>[\w^_]+)(?:\()?</p></div>'
    SIZE_REPLACEMENTS = [("Kb", "KiB"), ("Mb", "MiB"), ("Gb", "GiB")]

    LINK_PATTERN = r'<div class=".*premium-download">\s+<a href="(.+?)"'

    @staticmethod
    def filter_form(tag):
        action = parse_html_tag_attr_value("action", tag)
        return ".js" not in action if action else False

    FORM_PATTERN = filter_form
    FORM_INPUTS_MAP = {"op": re.compile(r"^download")}

    API_URL = "https://filejoker.net/zapi"

    def api_request(self, op, **kwargs):
        args = {"op": op}
        args.update(kwargs)
        return json.loads(self.load(self.API_URL, get=args))

    def handle_captcha(self, inputs):
        m = re.search(r'\$\.post\( "/ddl",\s*\{(.+?) \} \);', self.data)
        if m is not None:
            response = None
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()
            if captcha_key:
                self.captcha = recaptcha
                response = recaptcha.challenge(captcha_key)

            else:
                hcaptcha = HCaptcha(self.pyfile)
                captcha_key = hcaptcha.detect_key()
                if captcha_key:
                    self.captcha = hcaptcha
                    response = hcaptcha.challenge(captcha_key)

                elif (
                    re.search(r'data-sitekey="d1d53ad768bbEskdfm32Mal"', self.data)
                    is not None
                ):
                    xcaptcha = XCaptcha(self.pyfile)
                    response = xcaptcha.challenge()

            if response is not None:
                captcha_inputs = {}
                for _i in m.group(1).split(","):
                    _k, _v = _i.split(":", 1)
                    _k = _k.strip('" ')
                    if "g-recaptcha-response" in _v:
                        _v = response + "1111"

                    captcha_inputs[_k] = _v.strip('" ')

                self.req.http.c.setopt(
                    pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"]
                )

                html = self.load(
                    urllib.parse.urljoin(self.pyfile.url, "/ddl"),
                    post=captcha_inputs,
                    ref=self.pyfile.url
                )

                self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

                if html == "OK":
                    self.captcha.correct()

                else:
                    self.retry_captcha()

            else:
                self.fail(self._("Unknown captcha type"))

    def handle_premium(self, pyfile):
        api_data = self.api_request(
            "download1",
            file_code=self.info["pattern"]["ID"],
            session=self.account.info["data"]["session"],
        )

        if "error" in api_data:
            if api_data["error"] == "no file":
                self.offline()

            else:
                self.fail(api_data["error"])

        pyfile.name = api_data["file_name"]
        pyfile.size = api_data["file_size"]

        api_data = self.api_request(
            "download2",
            file_code=self.info["pattern"]["ID"],
            download_id=api_data["download_id"],
            session=self.account.info["data"]["session"],
        )

        if "error" in api_data:
            self.fail(api_data["error"])

        self.link = api_data["direct_link"]
