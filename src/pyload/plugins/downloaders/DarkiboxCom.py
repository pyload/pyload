import json
import re

from ..base.downloader import BaseDownloader


class DarkiboxCom(BaseDownloader):
    __name__ = "DarkiboxCom"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?darkibox\.com/(?:d/|embed-)?(?P<ID>\w+)(?:\.html)?"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("api_key", "str", "Darkibox API key (optional)", ""),
        (
            "quality",
            "Lowest;Highest",
            "Preferred quality (for multi-quality MP4)",
            "Highest",
        ),
    ]

    __description__ = """Darkibox.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = []

    OFFLINE_PATTERN = r">File Not Found<|>The file was removed"

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1
        self.resume_download = True

    @staticmethod
    def _unpack(packed):
        """Unpack Dean Edwards' p.a.c.k.e.r. packed JavaScript."""
        m = re.search(
            r"eval\(function\(p,a,c,k,e,[dr]\)\{.*?\}\('(.+?)',(\d+),(\d+),'([^']+)'\.split\('\|'\)",
            packed,
            re.S,
        )
        if m is None:
            return None

        payload, radix, count, keywords = m.groups()
        radix = int(radix)
        count = int(count)
        keywords = keywords.split("|")

        def base_n(num, base):
            """Convert a number to a base-N string (supports up to base 62)."""
            digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if num < 0:
                return "-" + base_n(-num, base)
            result = []
            while num:
                result.append(digits[num % base])
                num //= base
            return "".join(reversed(result)) or "0"

        def replacer(match):
            word = match.group(0)
            try:
                index = int(word, 36) if radix <= 36 else int(word) if word.isdigit() else -1
            except ValueError:
                index = -1

            # Try to find the keyword index by converting the word from the
            # base used by the packer
            try:
                idx = int(word, radix) if radix <= 36 else 0
            except ValueError:
                idx = 0

            # The packer replaces each word token with keywords[index] if set
            for i, kw in enumerate(keywords):
                if base_n(i, radix) == word:
                    return kw if kw else word
            return word

        result = re.sub(r"\b\w+\b", replacer, payload)
        return result

    @staticmethod
    def _extract_video_url(unpacked):
        """Extract video URL from unpacked PlayerJS code.

        Handles three formats:
        - HLS: file:"https://...m3u8"
        - Multi-quality MP4: file:"[label1]url1,[label2]url2"
        - Direct URL: file:"https://...mp4"
        """
        m = re.search(r'file\s*:\s*"([^"]+)"', unpacked)
        if m is None:
            return None, None
        file_value = m.group(1)
        return file_value, None

    @staticmethod
    def _parse_multi_quality(file_value):
        """Parse [label]url multi-quality format.

        Returns list of (label, url) tuples sorted by label quality.
        """
        entries = re.findall(r"\[([^\]]+)\](https?://[^,\s\"]+)", file_value)
        return entries

    def _resolve_quality(self, entries):
        """Pick a URL from multi-quality entries based on config."""
        if not entries:
            return None

        def quality_key(entry):
            m = re.search(r"(\d+)", entry[0])
            return int(m.group(1)) if m else 0

        entries_sorted = sorted(entries, key=quality_key)
        desired = self.config.get("quality")
        if desired == "Lowest":
            return entries_sorted[0][1]
        else:
            return entries_sorted[-1][1]

    def _handle_api(self, file_code):
        """Try to get a direct link via the Darkibox API.

        Returns a download URL string on success, or None if the API key is
        not configured or the request fails.
        """
        api_key = self.config.get("api_key")
        if not api_key:
            return None

        self.log_debug("Trying Darkibox API...")

        # Fetch file info for the filename
        try:
            info_resp = self.load(
                "https://darkibox.com/api/file/info",
                get={"key": api_key, "file_code": file_code},
            )
            info_json = json.loads(info_resp)
            if info_json.get("status") == 200:
                result = info_json.get("result", {})
                if isinstance(result, list) and result:
                    result = result[0]
                title = result.get("title") or result.get("name")
                if title:
                    if not re.search(r"\.\w{2,5}$", title):
                        title += ".mp4"
                    self.pyfile.name = title
        except Exception as exc:
            self.log_debug(f"API file info failed: {exc}")

        # Fetch direct link
        try:
            dl_resp = self.load(
                "https://darkibox.com/api/file/direct_link",
                get={"key": api_key, "file_code": file_code},
            )
            dl_json = json.loads(dl_resp)
            if dl_json.get("status") == 200:
                result = dl_json.get("result", {})
                versions = result.get("versions", [])
                if versions:
                    url = versions[0].get("url")
                    if url:
                        self.log_debug(f"API direct link obtained: {url[:80]}...")
                        return url
        except Exception as exc:
            self.log_debug(f"API direct_link failed: {exc}")

        return None

    def _handle_embed(self, file_code):
        """Get the download URL via the embed flow (no API key needed).

        1. POST to /dl with embed parameters
        2. Unpack the packed JavaScript in the response
        3. Extract the video URL from the PlayerJS parameters
        """
        self.log_debug("Using embed flow...")

        embed_url = f"https://darkibox.com/embed-{file_code}.html"

        # Load the embed page first (sets cookies / referrer)
        self.load(embed_url)

        # POST to the /dl endpoint
        data = self.load(
            "https://darkibox.com/dl",
            post={
                "op": "embed",
                "file_code": file_code,
                "auto": "1",
            },
            ref=embed_url,
        )

        if not data:
            self.fail("Empty response from embed endpoint")

        # Try to find and unpack the packed JS
        unpacked = self._unpack(data)
        if unpacked is None:
            # Maybe the response contains the URL directly
            m = re.search(r'file\s*:\s*"([^"]+)"', data)
            if m is None:
                self.fail("Could not find packed JS or direct file URL in response")
            file_value = m.group(1)
        else:
            file_value, _ = self._extract_video_url(unpacked)
            if file_value is None:
                self.fail("Could not extract video URL from unpacked JS")

        # Determine URL type
        if re.search(r"\[.+?\]https?://", file_value):
            # Multi-quality MP4
            entries = self._parse_multi_quality(file_value)
            if not entries:
                self.fail("Could not parse multi-quality entries")
            url = self._resolve_quality(entries)
        else:
            # HLS m3u8 or direct URL
            url = file_value

        return url

    def process(self, pyfile):
        file_code = re.match(self.__pattern__, pyfile.url).group("ID")

        # Set a default filename
        pyfile.name = f"{file_code}.mp4"

        # Try API first if configured
        url = self._handle_api(file_code)

        # Fall back to embed flow
        if not url:
            url = self._handle_embed(file_code)

        if not url:
            self.fail("Could not obtain download URL")

        self.log_debug(f"Downloading from: {url[:80]}...")

        # Try to extract a nicer filename from the URL
        m = re.search(r"/([^/]+\.(?:mp4|mkv|avi|m3u8))(?:\?|$)", url, re.I)
        if m and pyfile.name == f"{file_code}.mp4":
            pyfile.name = m.group(1)

        self.download(url)
