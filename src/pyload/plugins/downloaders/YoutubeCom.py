# -*- coding: utf-8 -*-

import json
import operator
import os
import re
import subprocess
import time
import urllib.parse
from datetime import timedelta
from functools import reduce
from xml.dom.minidom import parseString as parse_xml

from pyload import PKGDIR
from pyload.core.network.exceptions import Abort, Skip
from pyload.core.network.http.http_request import HTTPRequest
from pyload.core.utils.convert import to_str
from pyload.core.utils.old import safename

from ..base.downloader import BaseDownloader
from ..helpers import exists, is_executable, renice, replace_patterns, which


def find_by_keyvalue(lst, key, value):
    """
    Find a key/value in a list of dicts

    :param lst: the list of dicts to search in
    :param key: name of the key to check for value
    :param value: value to search for
    :return: index of the found item inside lst or None
    """
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i

    else:
        return None


def try_get(data, *path):
    def get_one(src, what):
        if isinstance(src, dict) and isinstance(what, str):
            return src.get(what, None)
        elif isinstance(src, list) and type(what) is int:
            try:
                return src[what]
            except IndexError:
                return None
        elif callable(what):
            try:
                return what(src)
            except Exception:
                return None
        else:
            return None

    res = get_one(data, path[0])
    for item in path[1:]:
        if res is None:
            break
        res = get_one(res, item)

    return res


def codec_from_mime_codec(mime_codec):
    if mime_codec.startswith("mp4a.40"):
        codec = "aac"
    elif mime_codec in ("mp4a.a5", "mp4a.a6", "ec-3"):
        codec = "ac3"
    elif mime_codec in ("mp4a.a9", "mp4a.b2", "dtsx"):
        codec = "dts"
    elif mime_codec in ("opus", "mp4a.ad"):
        codec = "opus"
    elif mime_codec == "vorbis":
        codec = "vorbis"
    elif mime_codec.split(".")[0] == "vp8":
        codec = "vp8"
    elif mime_codec.split(".")[0] == "vp9":
        codec = "vp9"
    elif mime_codec.split(".")[0] == "av01":
        codec = "av1"
    elif mime_codec.split(".")[0] == "avc1":
        codec = "h264"
    else:
        codec = None  #: Unknown

    return codec


class Ffmpeg:
    _RE_DURATION = re.compile(rb"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2}),")
    _RE_TIME = re.compile(rb"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
    _RE_VERSION = re.compile(rb"ffmpeg version (.+?) ")

    CMD = None
    priority = 0
    streams = []
    start_time = (0, 0)
    output_filename = None
    error_message = ""

    def __init__(self, priority, plugin=None):
        self.plugin = plugin
        self.priority = priority

        self.streams = []
        self.start_time = (0, 0)
        self.output_filename = None
        self.error_message = ""

        self.find()

    @classmethod
    def find(cls):
        """
        Check for ffmpeg.
        """
        if cls.CMD is not None:
            return True

        try:
            if os.name == "nt":
                ffmpeg = (
                    os.path.join(PKGDIR, "lib", "ffmpeg.exe")
                    if is_executable(os.path.join(PKGDIR, "lib", "ffmpeg.exe"))
                    else "ffmpeg.exe"
                )

            else:
                ffmpeg = "ffmpeg"

            cmd = which(ffmpeg) or ffmpeg

            p = subprocess.Popen(
                [cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = (r.strip() if r else "" for r in p.communicate())
        except OSError:
            return False

        m = cls._RE_VERSION.search(out)
        if m is not None:
            cls.VERSION = m.group(1)

        cls.CMD = cmd

        return True

    @property
    def found(self):
        return self.CMD is not None

    def add_stream(self, streams):
        if isinstance(streams, list):
            self.streams.extend(streams)
        else:
            self.streams.append(streams)

    def set_start_time(self, start_time):
        self.start_time = start_time

    def set_output_filename(self, output_filename):
        self.output_filename = output_filename

    def run(self):
        if self.CMD is None or self.output_filename is None:
            return False

        maps = []
        args = []
        meta = []
        for i, stream in enumerate(self.streams):
            args.extend(["-i", stream[1]])
            maps.extend(["-map", "{}:{}:0".format(i, stream[0])])
            if stream[0] == "s":
                meta.extend(
                    ["-metadata:s:s:0:{}".format(i), "language={}".format(stream[2])]
                )

        args.extend(maps)
        args.extend(meta)
        args.extend(
            [
                "-y",
                "-vcodec",
                "copy",
                "-acodec",
                "copy",
                "-scodec",
                "copy",
                "-ss",
                "00:{}:{}.00".format(self.start_time[0], self.start_time[1]),
                "-sub_charenc",
                "utf-8",
            ]
        )

        call = [self.CMD] + args + [self.output_filename]
        self.plugin.log_debug("EXECUTE " + " ".join(call))

        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        renice(p.pid, self.priority)

        duration = self._find_duration(p)
        if duration:
            last_line = self._progress(p, duration)
        else:
            last_line = ""

        out, err = (r.strip() if r else "" for r in p.communicate())
        if err or p.returncode:
            self.error_message = last_line
            return False

        else:
            self.error_message = ""
            return True

    def _find_duration(self, process):
        duration = 0
        while True:
            line = process.stderr.readline()  #: ffmpeg writes to stderr

            #: Quit loop on eof
            if not line:
                break

            m = self._RE_DURATION.search(line)
            if m is not None:
                duration = sum(
                    int(v) * [60 * 60 * 100, 60 * 100, 100, 1][i]
                    for i, v in enumerate(m.groups())
                )
                break

        return duration

    def _progress(self, process, duration):
        line = b""
        last_line = b""
        while True:
            c = process.stderr.read(1)  #: ffmpeg writes to stderr

            #: Quit loop on eof
            if not c:
                break

            elif c == b"\r":
                last_line = line.strip(b"\r\n")
                line = b""
                m = self._RE_TIME.search(last_line)
                if m is not None:
                    current_time = sum(
                        int(v) * [60 * 60 * 100, 60 * 100, 100, 1][i]
                        for i, v in enumerate(m.groups())
                    )
                    if self.plugin:
                        progress = current_time * 100 // duration
                        self.plugin.pyfile.set_progress(progress)

            else:
                line += c
            continue

        return to_str(last_line)  #: Last line may contain error message


class YoutubeCom(BaseDownloader):
    __name__ = "YoutubeCom"
    __type__ = "downloader"
    __version__ = "0.88"
    __status__ = "testing"

    __pattern__ = r"https?://(?:[^/]*\.)?(?:youtu\.be/|youtube\.com/watch\?(?:.*&)?v=)[\w\-]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        (
            "quality",
            "144p;240p;360p;480p;720p;1080p;1440p;2160p;3072p;4320p",
            "Quality Setting",
            "720p",
        ),
        ("vfmt", "int", "Video FMT/ITAG Number (0 for auto)", 0),
        ("afmt", "int", "Audio FMT/ITAG Number (0 for auto)", 0),
        (".mp4", "bool", "Allow .mp4", True),
        (".flv", "bool", "Allow .flv", True),
        (".webm", "bool", "Allow .webm", True),
        (".mkv", "bool", "Allow .mkv", True),
        (".3gp", "bool", "Allow .3gp", False),
        ("aac", "bool", "Allow aac audio (DASH video only)", True),
        ("vorbis", "bool", "Allow vorbis audio (DASH video only)", True),
        ("opus", "bool", "Allow opus audio (DASH video only)", True),
        ("ac3", "bool", "Allow ac3 audio (DASH video only)", True),
        ("dts", "bool", "Allow dts audio (DASH video only)", True),
        ("3d", "bool", "Prefer 3D", False),
        ("60fps", "bool", "Allow 60 FPS video", False),
        ("subs_dl", "off;all_specified;first_available", "Download subtitles", "off"),
        (
            "subs_dl_langs",
            "str",
            "Subtitle <a href='https://sites.google.com/site/tomihasa/google-language-codes#interfacelanguage'>language codes</a> to download (comma separated)",
            "",
        ),
        ("auto_subs", "bool", "Allow machine generated subtitles", True),
        (
            "subs_translate",
            "str",
            "Translate subtitles to <a href='https://sites.google.com/site/tomihasa/google-language-codes#interfacelanguage'>language</a> (forces first_available)",
            "",
        ),
        (
            "subs_embed",
            "bool",
            "Embed subtitles inside the output file (.mp4 and .mkv only)",
            False,
        ),
        ("priority", "int", "ffmpeg process priority", 0),
    ]

    __description__ = """Youtube.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("spoob", "spoob@pyload.net"),
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    URL_REPLACEMENTS = [(r"youtu\.be/", "youtube.com/watch?v=")]

    def _decrypt_signature(self, encrypted_sig):
        """Turn the encrypted 's' field into a working signature"""
        sig_cache_id = (
            self.player_url
            + "_"
            + ".".join(str(len(part)) for part in encrypted_sig.split("."))
        )

        cache_info = self.db.retrieve("cache")
        cache_dirty = False

        if cache_info is None or cache_info.get("version") != self.__version__:
            cache_info = {"version": self.__version__, "cache": {}}
            cache_dirty = True

        if (
            sig_cache_id in cache_info["cache"]
            and time.time() < cache_info["cache"][sig_cache_id]["time"] + timedelta(hours=24).total_seconds()
        ):
            self.log_debug("Using cached decode function to decrypt the URL")

            def decrypt_func(s):
                return "".join(
                    s[_i] for _i in cache_info['cache'][sig_cache_id]['decrypt_map']
                )

            decrypted_sig = decrypt_func(encrypted_sig)

        else:
            player_data = self.load(self.player_url)

            m = (
                re.search(
                    r"\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(",
                    player_data,
                )
                or re.search(
                    r"\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(",
                    player_data,
                )
                or re.search(
                    r'\b(?P<sig>[a-zA-Z0-9$]{2})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
                    player_data,
                )
                or re.search(
                    r'(?P<sig>[a-zA-Z0-9$]+)\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
                    player_data,
                )
                or re.search(r"\.sig\|\|(?P<sig>[a-zA-Z0-9$]+)\(", player_data)
                or re.search(
                    r"\bc\s*&&\s*d\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(",
                    player_data,
                )
                or re.search(
                    r'(["\'])signature\1\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(', player_data
                )
            )

            try:
                function_name = m.group("sig")

            except (AttributeError, IndexError):
                self.fail(self._("Signature decode function name not found"))

            try:
                jsi = JSInterpreter(player_data)

                def decrypt_func(s):
                    return jsi.extract_function(function_name)([s])

                #: Since Youtube just scrambles the order of the characters in the signature
                #: and does not change any byte value, we can store just a transformation map as a cached function
                decrypt_map = [
                    ord(c)
                    for c in decrypt_func(
                        "".join(chr(x) for x in range(len(encrypted_sig)))
                    )
                ]
                cache_info["cache"][sig_cache_id] = {
                    "decrypt_map": decrypt_map,
                    "time": time.time(),
                }
                cache_dirty = True

                decrypted_sig = decrypt_func(encrypted_sig)

            except (JSInterpreterError, AssertionError) as exc:
                self.log_error(self._("Signature decode failed"), exc)
                self.fail(str(exc))

        #: Remove old records from cache
        for k in list(cache_info["cache"].keys()):
            if time.time() >= cache_info["cache"][k]["time"] + timedelta(hours=24).total_seconds():
                cache_info["cache"].pop(k, None)
                cache_dirty = True

        if cache_dirty:
            self.db.store("cache", cache_info)

        return decrypted_sig

    def _handle_video(self):
        use3d = self.config.get("3d")
        use60fps = self.config.get("60fps")
        desired_itag = self.config.get("vfmt")
        desired_quality = self.config.get("quality")

        def is_video(x):
            return "v" in x["type"]

        def allowed_suffix(x):
            return self.config.get(x["ext"], False)

        def allowed_fps(x):
            info = x["quality"].split("p")[1]
            fps, hdr = (info.split((" ")) + [""])[:2]
            allowed = fps != "60" or use60fps
            return allowed

        #: Build dictionary of supported itags (3D/2D)
        video_streams = [
            _i
            for _i, _s in enumerate(self.streams)
            if is_video(_s)
            and allowed_suffix(_s)
            and allowed_fps(_s)
            and _s["3d"] == use3d
        ]

        if not video_streams:
            self.fail(self._("No available video stream meets your preferences"))

        chosen_stream_index = None
        if desired_itag != 0:
            desired_stream = find_by_keyvalue(self.streams, "itag", desired_itag)
            is_3d = try_get(self.streams, desired_stream, "3d")

            self.log_debug(
                "DESIRED VIDEO STREAM: ITAG:{} (EXT:{} {}x{} 3D:{}) {}found, {}allowed".format(
                    desired_itag,
                    try_get(self.streams, desired_stream, "ext") or "n/a",
                    try_get(self.streams, desired_stream, "width") or 0,
                    try_get(self.streams, desired_stream, "height") or 0,
                    is_3d if is_3d is not None else "n/a",
                    "NOT " if desired_stream is None else "",
                    "" if desired_stream in video_streams else "NOT ",
                )
            )
            #: if found and allowed
            if desired_stream in video_streams:
                chosen_stream_index = desired_stream

        if chosen_stream_index is None:
            #: Return fmt nearest to desired quality
            def quality_distance(x, y):
                return abs(int(x.split("p")[0]) - int(y.split("p")[0]))

            chosen_stream_index = reduce(
                lambda x, y: x if quality_distance(self.streams[x]["quality"], desired_quality) <= quality_distance(self.streams[y]["quality"], desired_quality) else y,
                video_streams
            )

        chosen_stream = self.streams[chosen_stream_index]

        is_3d = try_get(chosen_stream, "3d")
        vmime, amime = ([x.strip() for x in chosen_stream["codecs"].split(",")] + [None])[:2]
        self.log_debug(
            "CHOSEN VIDEO STREAM: ITAG:{} ({}/{} {}x{} 3D:{} AUDIO:{})".format(
                try_get(chosen_stream, "itag"),
                try_get(chosen_stream, "ext") or "n/a",
                codec_from_mime_codec(vmime) or "unknown",
                try_get(chosen_stream, "width") or 0,
                try_get(chosen_stream, "height") or 0,
                is_3d if is_3d is not None else "n/a",
                "None" if amime is None else (codec_from_mime_codec(amime) or "unknown"),
            )
        )

        url = chosen_stream["url"]

        if chosen_stream["signature"]:
            if chosen_stream["has_encrypted_signature"]:
                signature = self._decrypt_signature(chosen_stream["signature"])

            else:
                signature = chosen_stream["signature"]

            url += "&{}={}".format(chosen_stream["signature_query_param"], signature)

        if "&ratebypass=" not in url:
            url += "&ratebypass=yes"

        file_suffix = try_get(chosen_stream, "ext") or "flv"

        if "a" not in chosen_stream["type"]:
            file_suffix = ".video" + file_suffix

        self.pyfile.name = self.file_name + file_suffix

        try:
            filename = self.download(url, disposition=False)
        except Skip as exc:
            filename = os.path.join(
                self.pyload.config.get("general", "storage_folder"),
                self.pyfile.package().folder,
                self.pyfile.name,
            )
            self.log_info(
                self._("Download skipped: {} due to {}").format(self.pyfile.name, exc)
            )

        return filename, chosen_stream_index

    def _handle_audio(self, video_stream_index=None):
        def is_audio(x):
            return x["type"] == "a"

        def allowed_codec(x):
            mime_codec = x["codecs"].lower()
            codec = codec_from_mime_codec(mime_codec)
            if codec is None:
                return False
            else:
                return self.config.get(codec)

        def allowed_suffix(x):
            if video_stream_index is None:
                return self.config.get(".mkv") or self.config.get(x["ext"])

            else:
                return (
                    self.config.get(".mkv")
                    or self.config.get(x["ext"])
                    and x["ext"] == self.streams[video_stream_index]["ext"]
                )

        chosen_stream_index = None
        desired_itag = self.config.get("afmt", 0)
        if desired_itag != 0:
            desired_stream = find_by_keyvalue(self.streams, "itag", desired_itag)
            if desired_stream is None or not is_audio(desired_stream):
                self.log_warning(
                    self._("AUDIO ITAG {} unknown, using default").format(desired_itag)
                )

            else:
                chosen_stream_index = desired_stream

        if chosen_stream_index is None:
            #: Build dictionary of supported audio itags
            audio_streams = [
                _i
                for _i, _s in enumerate(self.streams)
                if is_audio(_s)
                and allowed_codec(_s)
                and allowed_suffix(_s)
            ]

            if not audio_streams:
                self.fail(self._("No available audio stream meets your preferences"))

            chosen_stream_index = sorted(audio_streams, key=lambda x: self.streams[x]["bitrate"])[0]

        chosen_stream = self.streams[chosen_stream_index]
        self.log_debug(
            "CHOSEN AUDIO STREAM: ITAG:{} ({} {} bitrate: {})".format(
                chosen_stream["itag"],
                chosen_stream["ext"],
                codec_from_mime_codec(chosen_stream["codecs"]),
                chosen_stream["bitrate"],
            )
        )

        url = chosen_stream["url"]

        if chosen_stream["signature"]:
            if chosen_stream["has_encrypted_signature"]:
                signature = self._decrypt_signature(chosen_stream["signature"])

            else:
                signature = chosen_stream["signature"]

            url += "&{}={}".format(chosen_stream["signature_query_param"], signature)

        if "&ratebypass=" not in url:
            url += "&ratebypass=yes"

        file_suffix = ".audio" + (".webm" if chosen_stream["ext"] == ".webm" else ".m4a")

        self.pyfile.name = self.file_name + file_suffix

        try:
            filename = self.download(url, disposition=False)
        except Skip as exc:
            filename = os.path.join(
                self.pyload.config.get("general", "storage_folder"),
                self.pyfile.package().folder,
                self.pyfile.name,
            )
            self.log_info(
                self._("Download skipped: {} due to {}").format(self.pyfile.name, exc)
            )

        return filename, chosen_stream_index

    def _handle_subtitles(self):
        def timedtext_to_srt(timedtext):
            def _format_srt_time(millisec):
                sec, milli = divmod(millisec, 1000)
                m, s = divmod(int(sec), 60)
                h, m = divmod(m, 60)
                return "{:02}:{:02}:{:02},{}".format(h, m, s, milli)

            srt = ""
            dom = parse_xml(timedtext)
            body = dom.getElementsByTagName("body")[0]
            paras = body.getElementsByTagName("p")
            subtitles = []
            for para in paras:
                try:
                    start_time = int(para.attributes["t"].value)
                    end_time = int(para.attributes["t"].value) + int(
                        para.attributes["d"].value
                    )
                except KeyError:
                    continue

                subtitle_text = ""
                words = para.getElementsByTagName("s")
                if words:
                    subtitle_text = "".join(
                        [str(word.firstChild.data) for word in words]
                    )

                else:
                    for child in para.childNodes:
                        if child.nodeName == "br":
                            subtitle_text += "\n"
                        elif child.nodeName == "#text":
                            subtitle_text += str(child.data)

                if subtitle_text.strip():
                    subtitles.append(
                        {"start": start_time, "end": end_time, "text": subtitle_text}
                    )
                else:
                    continue

            for line_num in range(len(subtitles)):
                start_time = subtitles[line_num]["start"]
                try:
                    end_time = min(
                        subtitles[line_num]["end"], subtitles[line_num + 1]["start"]
                    )
                except IndexError:
                    end_time = subtitles[line_num]["end"]

                subtitle_text = subtitles[line_num]["text"]

                subtitle_element = (
                    str(line_num + 1)
                    + "\n"
                    + _format_srt_time(start_time)
                    + " --> "
                    + _format_srt_time(end_time)
                    + "\n"
                    + subtitle_text
                    + "\n\n"
                )
                srt += subtitle_element

            return srt

        srt_files = []
        try:
            subs = self.player_response["captions"]["playerCaptionsTracklistRenderer"][
                "captionTracks"
            ]
            subtitles_info = {
                subtitle["languageCode"]:
                    (
                        urllib.parse.unquote(subtitle["baseUrl"], encoding="unicode-escape") + "&fmt=3",
                        subtitle["vssId"].startswith("a."),
                        subtitle["isTranslatable"],
                    )
                for subtitle in subs
            }
            self.log_debug("AVAILABLE SUBTITLES: {}".format(list(subtitles_info.keys()) or "None"))

        except KeyError:
            self.log_debug("AVAILABLE SUBTITLES: None")
            return srt_files

        subs_dl = self.config.get("subs_dl")
        if subs_dl != "off":
            subs_translate = self.config.get("subs_translate").strip()
            auto_subs = self.config.get("auto_subs")
            subs_dl = "first_available" if subs_translate != "" else subs_dl
            subs_dl_langs = [
                lang.strip()
                for lang in self.config.get("subs_dl_langs", "").split(",")
                if lang.strip()
            ]

            if subs_dl_langs:
                # Download only listed subtitles (`subs_dl_langs` config gives the priority)
                for lang in subs_dl_langs:
                    if lang in subtitles_info:
                        subtitle_code = (
                            lang if subs_translate == "" else subs_translate
                        )

                        if auto_subs is False and subtitles_info[lang][1] is True:
                            self.log_warning(
                                self._("Skipped machine generated subtitle: {}").format(lang)
                            )
                            continue

                        subtitle_url = subtitles_info[lang][0]
                        if subs_translate:
                            if subtitles_info[lang][2]:  #: Translatable?
                                subtitle_url += "&tlang={}".format(subs_translate)
                            else:
                                self.log_warning(
                                    self._("Skipped non translatable subtitle: {}").format(lang)
                                )
                                continue  #: No, try next one

                        srt_filename = os.path.join(
                            self.pyload.config.get("general", "storage_folder"),
                            self.pyfile.package().folder,
                            self.file_name + "." + subtitle_code + ".srt",
                        )

                        if (
                            self.pyload.config.get("download", "skip_existing")
                            and exists(srt_filename)
                            and os.stat(srt_filename).st_size != 0
                        ):
                            self.log_info(
                                "Download skipped: {} due to File exists".format(
                                    os.path.basename(srt_filename)
                                )
                            )
                            srt_files.append((srt_filename, subtitle_code))
                            continue

                        timed_text = self.load(subtitle_url, decode=False)
                        srt = timedtext_to_srt(timed_text)

                        with open(srt_filename, mode="w") as fp:
                            fp.write(srt)
                        self.set_permissions(srt_filename)
                        self.log_debug(
                            "Saved subtitle: {}".format(os.path.basename(srt_filename))
                        )
                        srt_files.append((srt_filename, lang))
                        if subs_dl == "first_available":
                            break

            else:
                # Download any available subtitle
                for subtitle in subtitles_info.items():
                    if auto_subs is False and subtitle[1][1] is True:
                        self.log_warning(
                            self._("Skipped machine generated subtitle: {}").format(subtitle[0])
                        )
                        continue

                    subtitle_code = (
                        subtitle[0] if subs_translate == "" else subs_translate
                    )

                    subtitle_url = subtitle[1][0]
                    if subs_translate:
                        if subtitle[1][2]:  #: Translatable?
                            subtitle_url += "&tlang={}".format(subs_translate)
                        else:
                            self.log_warning(
                                self._("Skipped non translatable subtitle: {}").format(subtitle[0])
                            )
                            continue  #: No, try next one

                    srt_filename = os.path.join(
                        self.pyload.config.get("general", "storage_folder"),
                        self.pyfile.package().folder,
                        os.path.splitext(self.file_name)[0]
                        + "."
                        + subtitle_code
                        + ".srt",
                    )

                    if (
                        self.pyload.config.get("download", "skip_existing")
                        and exists(srt_filename)
                        and os.stat(srt_filename).st_size != 0
                    ):
                        self.log_info(
                            "Download skipped: {} due to File exists".format(
                                os.path.basename(srt_filename)
                            )
                        )
                        srt_files.append((srt_filename, subtitle_code))
                        continue

                    timed_text = self.load(subtitle_url, decode=False)
                    srt = timedtext_to_srt(timed_text)

                    with open(srt_filename, mode="w") as fp:
                        fp.write(srt)
                    self.set_permissions(srt_filename)

                    self.log_debug(
                        "Saved subtitle: {}".format(os.path.basename(srt_filename))
                    )
                    srt_files.append((srt_filename, subtitle_code))
                    if subs_dl == "first_available":
                        break

        return srt_files

    def _postprocess(self, video_filename, audio_filename, subtitles_files):
        final_filename = video_filename
        subs_embed = self.config.get("subs_embed")

        self.pyfile.set_custom_status("postprocessing")
        self.pyfile.set_progress(0)

        if self.ffmpeg.found:
            if audio_filename is not None:
                video_suffix = os.path.splitext(video_filename)[1]
                final_filename = os.path.join(
                    os.path.dirname(video_filename),
                    self.file_name
                    + (
                        video_suffix
                        if video_suffix == os.path.splitext(audio_filename)[1]
                        else ".mkv"
                    ),
                )

                self.ffmpeg.add_stream(("v", video_filename))
                self.ffmpeg.add_stream(("a", audio_filename))

                if subtitles_files and subs_embed:
                    for subtitle in subtitles_files:
                        self.ffmpeg.add_stream(("s",) + subtitle)

                self.ffmpeg.set_start_time(self.start_time)
                self.ffmpeg.set_output_filename(final_filename)

                self.pyfile.name = os.path.basename(final_filename)
                self.pyfile.size = os.path.getsize(video_filename) + os.path.getsize(
                    audio_filename
                )  #: Just an estimate

                if self.ffmpeg.run():
                    self.remove(video_filename, try_trash=False)
                    self.remove(audio_filename, try_trash=False)
                    if subtitles_files and subs_embed:
                        for subtitle in subtitles_files:
                            self.remove(subtitle[0])

                else:
                    self.log_warning(self._("ffmpeg error"), self.ffmpeg.error_message)
                    final_filename = video_filename

            elif (
                self.start_time[0] != 0
                or self.start_time[1] != 0
                or subtitles_files
                and subs_embed
            ):
                inputfile = video_filename + "_"
                final_filename = video_filename
                os.rename(video_filename, inputfile)

                self.ffmpeg.add_stream(("v", video_filename))
                self.ffmpeg.set_start_time(self.start_time)

                if subtitles_files and subs_embed:
                    for subtitle in subtitles_files:
                        self.ffmpeg.add_stream(("s", subtitle))

                self.pyfile.name = os.path.basename(final_filename)
                self.pyfile.size = os.path.getsize(inputfile)  #: Just an estimate

                if self.ffmpeg.run():
                    self.remove(inputfile, try_trash=False)
                    if subtitles_files and subs_embed:
                        for subtitle in subtitles_files:
                            self.remove(subtitle[0])

                else:
                    self.log_warning(self._("ffmpeg error"), self.ffmpeg.error_message)

        else:
            if audio_filename is not None:
                self.log_warning(
                    "ffmpeg is not installed, video and audio files will not be merged"
                )

            if subtitles_files and self.config.get("subs_embed"):
                self.log_warning(
                    "ffmpeg is not installed, subtitles files will not be embedded"
                )

        self.pyfile.set_progress(100)

        self.set_permissions(final_filename)

        return final_filename

    def setup(self):
        self.resume_download = True
        self.chunk_limit = -1
        self.multi_dl = True

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = HTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.request_factory.get_options(),
            limit=5_000_000,
        )

    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)
        self.data = self.load(pyfile.url)

        url, inputs = self.parse_html_form('action="https://consent.youtube.com/s"')
        if url is not None:
            self.data = self.load(url, post=inputs)

        m = re.search(
            r'"playabilityStatus":{"status":"(\w+)",(:?"(?:reason":|messages":\[)"([^"]+))?',
            self.data,
        )
        if m is None:
            self.log_warning(self._("Playability status pattern not found"))

        else:
            if m.group(1) != "OK":
                if m.group(2):
                    self.log_error(m.group(2))
                self.offline()

        if (
            "We have been receiving a large volume of requests from your network."
            in self.data
        ):
            self.temp_offline()

        m = re.search(r"ytplayer.config = ({.+?});", self.data)
        if m is not None:
            self.player_config = json.loads(m.group(1))
            self.player_response = json.loads(
                self.player_config["args"]["player_response"]
            )

        else:
            m = re.search(r"ytInitialPlayerResponse = ({.+?});", self.data)
            if m is not None:
                self.player_config = json.loads(m.group(1))
                self.player_response = self.player_config

            else:
                self.fail(self._("Player config pattern not found"))

        m = re.search(r'"jsUrl"\s*:\s*"(.+?)"', self.data) or re.search(
            r'"assets":.+?"js":\s*"(.+?)"', self.data
        )
        if m is None:
            self.fail(self._("Player URL pattern not found"))

        self.player_url = self.fixurl(m.group(1))

        if not self.player_url.endswith(".js"):
            self.fail(self._("Unsupported player type {}").format(self.player_url))

        self.ffmpeg = Ffmpeg(self.config.get("priority"), self)

        #: Set file name
        self.file_name = self.player_response['videoDetails']['title']

        #: Check for start time
        self.start_time = (0, 0)
        m = re.search(r"t=(?:(\d+)m)?(\d+)s", pyfile.url)
        if self.ffmpeg and m:
            self.start_time = tuple(
                map(lambda _x: 0 if _x is None else int(_x), m.groups())
            )
            self.file_name += " (starting at {}m{}s)".format(
                self.start_time[0],
                self.start_time[1],
            )

        #: Cleaning invalid characters from the file name
        self.file_name = safename(self.file_name)

        #: Parse available streams
        streams = []
        for path in [("args", "url_encoded_fmt_stream_map"), ("args", "adaptive_fmts")]:
            item = try_get(self.player_config, *path)
            if item is not None:
                strms = [urllib.parse.parse_qs(_s) for _s in item.split(",")]
                strms = [dict((k, v[0]) for k, v in _d.items()) for _d in strms]
                streams.extend(strms)
        streams.extend(try_get(self.player_response, "streamingData", "formats") or [])
        streams.extend(
            try_get(self.player_response, "streamingData", "adaptiveFormats") or []
        )

        def get_ext(mime):
            return "." + mime.split(";")[0].split("/")[1]

        def get_codecs(mime):
            return re.search('"(.+?)"', mime.split(";")[1]).group(1)

        self.streams = {}
        for stream in streams:
            itag = int(stream["itag"])
            url = stream.get("url", None)
            if url is None:
                cipher = stream.get("cipher") or stream.get("signatureCipher")
                if cipher is not None:
                    url_data = urllib.parse.parse_qs(cipher)
                    url_data = dict((k, v[0]) for k, v in url_data.items())
                    url = url_data.get("url")
                    if url is None:
                        continue
                    else:
                        stream.update(url_data)

                else:
                    continue

            if itag not in self.streams:
                self.streams[itag] = {
                    "itag": itag,
                    "url": url,
                    "size": int(stream.get("contentLength", 0)),
                    "ext": get_ext(stream["mimeType"]),
                    "signature": try_get(stream, "s", 0) or stream.get("s", stream.get("sig", None)),
                    "has_encrypted_signature": "s" in stream,
                    "signature_query_param": try_get(stream, "sp", 0) or stream.get("sp", "signature"),
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                    "quality": stream.get("qualityLabel"),
                    "codecs": get_codecs(stream["mimeType"]),
                    "bitrate": stream.get("bitrate"),
                    "3d": "stereoLayout" in stream,
                    "type": ("a" if "audioChannels" in stream else "") + ("v" if "fps" in stream else ""),
                }

        self.streams = list(self.streams.values())
        self.log_debug("AVAILABLE STREAMS: {}".format([_s["itag"] for _s in self.streams]))

        video_filename, video_stream_index = self._handle_video()

        has_audio = "a" in self.streams[video_stream_index]["type"]
        if not has_audio:
            audio_filename, audio_stream_index = self._handle_audio(video_stream_index)

        else:
            audio_filename = None

        subtitles_files = self._handle_subtitles()

        final_filename = self._postprocess(
            video_filename, audio_filename, subtitles_files
        )

        #: Everything is finished and final name can be set
        pyfile.name = os.path.basename(final_filename)
        pyfile.size = os.path.getsize(final_filename)
        self.last_download = final_filename


"""Credit to this awesome piece of code below goes to the 'youtube_dl' project, kudos!"""


class JSInterpreterError(Exception):
    pass


class JSInterpreter:
    def __init__(self, code, objects=None):
        self._OPERATORS = [
            ("|", operator.or_),
            ("^", operator.xor),
            ("&", operator.and_),
            (">>", operator.rshift),
            ("<<", operator.lshift),
            ("-", operator.sub),
            ("+", operator.add),
            ("%", operator.mod),
            ("/", operator.truediv),
            ("*", operator.mul),
        ]
        self._ASSIGN_OPERATORS = [(op + "=", opfunc) for op, opfunc in self._OPERATORS]
        self._ASSIGN_OPERATORS.append(("=", lambda cur, right: right))
        self._VARNAME_PATTERN = r"[a-zA-Z_$][a-zA-Z_$0-9]*"

        if objects is None:
            objects = {}
        self.code = code
        self._functions = {}
        self._objects = objects

    def interpret_statement(self, stmt, local_vars, allow_recursion=100):
        if allow_recursion < 0:
            raise JSInterpreterError("Recursion limit reached")

        should_abort = False
        stmt = stmt.lstrip()
        stmt_m = re.match(r"var\s", stmt)
        if stmt_m:
            expr = stmt[len(stmt_m.group(0)):]

        else:
            return_m = re.match(r"return(?:\s+|$)", stmt)
            if return_m:
                expr = stmt[len(return_m.group(0)):]
                should_abort = True
            else:
                # Try interpreting it as an expression
                expr = stmt

        v = self.interpret_expression(expr, local_vars, allow_recursion)
        return v, should_abort

    def interpret_expression(self, expr, local_vars, allow_recursion):
        expr = expr.strip()

        if expr == "":  #: Empty expression
            return None

        if expr.startswith("("):
            parens_count = 0
            for m in re.finditer(r"[()]", expr):
                if m.group(0) == "(":
                    parens_count += 1
                else:
                    parens_count -= 1
                    if parens_count == 0:
                        sub_expr = expr[1:m.start()]
                        sub_result = self.interpret_expression(
                            sub_expr, local_vars, allow_recursion
                        )
                        remaining_expr = expr[m.end():].strip()
                        if not remaining_expr:
                            return sub_result
                        else:
                            expr = json.dumps(sub_result) + remaining_expr
                        break
            else:
                raise JSInterpreterError("Premature end of parens in {!r}".format(expr))

        for op, opfunc in self._ASSIGN_OPERATORS:
            m = re.match(
                r"(?x)(?P<out>{})(?:\[(?P<index>[^\]]+?)\])?\s*{}(?P<expr>.*)$".format(
                    self._VARNAME_PATTERN, re.escape(op)
                ),
                expr,
            )
            if m is None:
                continue
            right_val = self.interpret_expression(
                m.group("expr"), local_vars, allow_recursion - 1
            )

            if m.groupdict().get("index"):
                lvar = local_vars[m.group("out")]
                idx = self.interpret_expression(
                    m.group("index"), local_vars, allow_recursion
                )
                assert isinstance(idx, int)
                cur = lvar[idx]
                val = opfunc(cur, right_val)
                lvar[idx] = val
                return val
            else:
                cur = local_vars.get(m.group("out"))
                val = opfunc(cur, right_val)
                local_vars[m.group("out")] = val
                return val

        if expr.isdigit():
            return int(expr)

        var_m = re.match(
            r"(?!if|return|true|false)(?P<name>{})$".format(self._VARNAME_PATTERN), expr
        )
        if var_m:
            return local_vars[var_m.group("name")]

        try:
            return json.loads(expr)
        except ValueError:
            pass

        m = re.match(
            r"(?P<var>{})\.(?P<member>[^(]+)(?:\(+(?P<args>[^()]*)\))?$".format(
                self._VARNAME_PATTERN
            ),
            expr,
        )
        if m is not None:
            variable = m.group("var")
            member = m.group("member")
            arg_str = m.group("args")

            if variable in local_vars:
                obj = local_vars[variable]
            else:
                if variable not in self._objects:
                    self._objects[variable] = self.extract_object(variable)
                obj = self._objects[variable]

            if arg_str is None:
                # Member access
                if member == "length":
                    return len(obj)
                return obj[member]

            assert expr.endswith(")")
            # Function call
            if arg_str == "":
                argvals = tuple()
            else:
                argvals = tuple(
                    self.interpret_expression(v, local_vars, allow_recursion)
                    for v in arg_str.split(",")
                )

            if member == "split":
                assert argvals == ("",)
                return list(obj)

            if member == "join":
                assert len(argvals) == 1
                return argvals[0].join(obj)

            if member == "reverse":
                assert len(argvals) == 0
                obj.reverse()
                return obj

            if member == "slice":
                assert len(argvals) == 1
                return obj[argvals[0]:]

            if member == "splice":
                assert isinstance(obj, list)
                index, how_many = argvals
                res = []
                for i in range(index, min(index + how_many, len(obj))):
                    res.append(obj.pop(index))
                return res

            return obj[member](argvals)

        m = re.match(r"(?P<in>{})\[(?P<idx>.+)\]$".format(self._VARNAME_PATTERN), expr)
        if m is not None:
            val = local_vars[m.group("in")]
            idx = self.interpret_expression(
                m.group("idx"), local_vars, allow_recursion - 1
            )
            return val[idx]

        for op, opfunc in self._OPERATORS:
            m = re.match(r"(?P<x>.+?){}(?P<y>.+)".format(re.escape(op)), expr)
            if m is None:
                continue

            x, abort = self.interpret_statement(
                m.group("x"), local_vars, allow_recursion - 1
            )
            if abort:
                raise JSInterpreterError(
                    "Premature left-side return of {} in {!r}".format(op, expr)
                )

            y, abort = self.interpret_statement(
                m.group("y"), local_vars, allow_recursion - 1
            )
            if abort:
                raise JSInterpreterError(
                    "Premature right-side return of {} in {!r}".format(op, expr)
                )

            return opfunc(x, y)

        m = re.match(
            r"^(?P<func>{})\((?P<args>[a-zA-Z0-9_$,]+)\)$".format(
                self._VARNAME_PATTERN
            ),
            expr,
        )
        if m is not None:
            fname = m.group("func")
            argvals = tuple(
                int(v) if v.isdigit() else local_vars[v]
                for v in m.group("args").split(",")
            )
            if fname not in self._functions:
                self._functions[fname] = self.extract_function(fname)
            return self._functions[fname](argvals)

        raise JSInterpreterError("Unsupported JS expression {!r}".format(expr))

    def extract_object(self, objname):
        obj = {}
        obj_m = re.search(
            r"(?:var\s+)?{}\s*=\s*{{\s*(?P<fields>([a-zA-Z$0-9]+\s*:\s*function\(.*?\)\s*{{.*?}}(?:,\s*)?)*)}}\s*;".format(
                re.escape(objname)
            ),
            self.code,
        )
        fields = obj_m.group("fields")
        # Currently, it only supports function definitions
        fields_m = re.finditer(
            r"(?P<key>[a-zA-Z$0-9]+)\s*:\s*function\((?P<args>[a-z,]+)\){(?P<code>[^}]+)}",
            fields,
        )
        for field in fields_m:
            argnames = field.group("args").split(",")
            obj[field.group("key")] = self.build_function(argnames, field.group("code"))

        return obj

    def extract_function(self, function_name):
        func_m = re.search(
            r"(?x)(?:function\s+{}|[{{;,]\s*{}\s*=\s*function|var\s+{}\s*=\s*function)\s*\((?P<args>[^)]*)\)\s*{{(?P<code>[^}}]+)}}".format(
                re.escape(function_name),
                re.escape(function_name),
                re.escape(function_name),
            ),
            self.code,
        )
        if func_m is None:
            raise JSInterpreterError(
                "Could not find JS function {!r}".format(function_name)
            )

        argnames = func_m.group("args").split(",")

        return self.build_function(argnames, func_m.group("code"))

    def call_function(self, function_name, *args):
        f = self.extract_function(function_name)
        return f(args)

    def build_function(self, argnames, code):
        def resf(argvals):
            local_vars = dict(zip(argnames, argvals))
            for stmt in code.split(";"):
                res, abort = self.interpret_statement(stmt, local_vars)
                if abort:
                    break
            return res

        return resf
