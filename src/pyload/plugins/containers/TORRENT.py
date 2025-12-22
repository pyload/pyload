# -*- coding: utf-8 -*-
import base64
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Final, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from pyload.core.network.request_factory import get_url
from pyload.core.utils.convert import to_str
from pyload.core.utils.fs import safename

from ..base.container import BaseContainer


class TORRENT(BaseContainer):
    __name__ = "TORRENT"
    __type__ = "container"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r"(?:file|https?)://.+\.torrent|magnet:\?.+|(?!(?:file|https?)://).+\.(?:torrent|magnet)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """TORRENT container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    CONTAINER_PATTERN = r"(?!(?:file|https?)://).+\.(?:torrent|magnet)"
    DECRYPTER_PATTERN = r"(?:file|https?)://.+\.torrent|magnet:\?.+"

    def process(self, pyfile):
        if re.match(self.DECRYPTER_PATTERN, pyfile.url) is not None:
            self.log_error(self._("No plugin is associated with torrents / magnets"),
                           self._("Please go to plugin settings -> TORRENT and select your preferred plugin"))

            self.fail(self._("No plugin is associated with torrents / magnets"))

        elif re.match(self.CONTAINER_PATTERN, pyfile.url) is not None:
            return super().process(pyfile)

    def decrypt(self, pyfile):
        fs_filename = os.fsencode(pyfile.url)
        with open(fs_filename, mode="rb") as fp:
            torrent_content = fp.read()

        time_ref = "{:.2f}".format(time.time())[-6:].replace(".", "")
        pack_name = "torrent {}".format(time_ref)

        if pyfile.url.endswith(".magnet"):
            if torrent_content.startswith(b"magnet:?"):
                self.packages.append((pyfile.package().name, [to_str(torrent_content)], pyfile.package().folder))

        elif pyfile.url.endswith(".torrent"):
            m = re.search(rb"name(\d+):", torrent_content)
            if m:
                m = re.search(
                    b"".join((b"name", m.group(1), b":(.{", m.group(1), b"})")),
                    torrent_content
                )
                if m:
                    pack_name = safename(to_str(m.group(1)))

            torrent_filename = os.path.join(
                self.pyload.tempdir, "tmp_{}.torrent".format(pack_name)
            )
            with open(torrent_filename, mode="wb") as fp:
                fp.write(torrent_content)

            self.packages.append(
                (
                    pack_name,
                    ["file://{}".format(urllib.request.pathname2url(torrent_filename))],
                    pack_name,
                )
            )


def bdecode(data: bytes) -> tuple[Union[dict, list, int, bytes], bytes]:
    """
    Decodes a single bencoded element from the given bytes-like object.
    Bencoding is a serialization format used by the BitTorrent protocol.
    This function supports decoding integers, byte strings, lists, and dictionaries.

    Args:
        data (bytes): The bencoded data to decode. Must start with a valid bencode type indicator.

    Returns:
        tuple: A tuple containing the decoded Python object (int, bytes, list, or dict) and the remaining bytes after the decoded element.

    Raises:
        ValueError: If the input data is malformed or does not conform to the bencode specification.

    Supported bencode types:
        - Integers: b"i<integer>e"
        - Byte strings: b"<length>:<data>"
        - Lists: b"l<elements>e"
        - Dictionaries: b"d<key-value pairs>e"
    """
    if data[0] == b"i":  #: integer
        m = re.match(b"i(-?\\d+)e", data)
        if m is None:
            raise ValueError("Malformed bencoded integer.")

        return int(m.group(1)), data[m.span()[1]:]

    elif data[0] in b"dl":  #: list or dictionary
        lst: list = []
        rest: bytes = data[1:]
        while not rest[0] == b"e":
            elem, rest = bdecode(rest)
            lst.append(elem)

        rest = rest[1:]
        if data[0] == b"l":
            #: list
            return lst, rest
        else:
            #: dictionary
            return {i: j for i, j in zip(lst[::2], lst[1::2])}, rest

    elif data[0].isdigit():  #: string
        m = re.match(b"(\\d+):", data)
        if m is None:
            raise ValueError("Malformed bencoded string.")

        length: int = int(m.group(1))
        start: int = m.span()[1]
        end: int = start + length
        return data[start:end], data[end:]

    else:
        raise ValueError("Malformed bencoded input.")


def bencode(x: Union[dict, list, int, bytes]) -> bytes:
    """
    Encodes a Python object using the bencode serialization format.

    Bencode is used primarily in torrent files. The function supports encoding of the following types:
    - int: Encoded as b'i<integer>e'
    - bytes: Encoded as b'<length>:<bytes>'
    - str: Encoded as b'<length>:<utf-8-bytes>'
    - list: Encoded as b'l<item1><item2>...e'
    - dict: Encoded as b'd<key1><value1><key2><value2>...e' (keys are sorted)

    Args:
        x (int, bytes, str, list, dict): The object to bencode.

    Returns:
        bytes: The bencoded representation of the input.

    Raises:
        TypeError: If the input type is not supported for bencoding.
    """
    if isinstance(x, int):
        return b"i%de" % x
    elif isinstance(x, bytes):
        return b"%d:%s" % (len(x), x)
    elif isinstance(x, str):
        x = x.encode()
        return b"%d:%s" % (len(x), x)
    elif isinstance(x, list):
        return b"l" + b"".join([bencode(i) for i in x]) + b"e"
    elif isinstance(x, dict):
        items = sorted(x.items())
        return b"d" + b"".join([bencode(k) + bencode(v) for k, v in items]) + b"e"
    else:
        raise TypeError("Unsupported type for bencoding: %s" % type(x))

def get_info_hash(input_data: object) -> str:
    """
    Extracts the info hash from a torrent file, magnet URL, or binary content.

    :param input_data: A magnet URL, torrent URL, file-like object, or binary content.
    :return: The info hash as a hexadecimal string.
    """
    def _get_info_section_from_torrent(torrent_content: bytes) -> tuple[int, int]:
        """
        Identifies the start and end positions of the 'info' section within a torrent file's binary content.

        Args:
            torrent_content (bytes): The binary content of a torrent file.

        Returns:
            tuple[int, int]: A tuple containing the start and end positions of the 'info' section within the binary content.

        Raises:
            TypeError: If the input is not of type 'bytes'.
            ValueError: If the 'info' section is not found or is malformed.
        """
        if not isinstance(torrent_content, bytes):
            raise TypeError("torrent_content must be of type 'bytes'.")

        # Find the start of the 'info' dictionary
        INFO_KEY = b'4:info'

        start = torrent_content.find(INFO_KEY)
        if start == -1:
            raise ValueError("'info' section not found in torrent content.")

        # The info dict starts after the key and should be a bencoded dictionary (starts with 'd')
        info_start = start + len(INFO_KEY)
        if torrent_content[info_start:info_start+1] != b'd':
            raise ValueError("'info' section does not start with a dictionary.")

        # Find the end of the info dictionary by bdecode
        def find_dict_end(data: bytes, offset: int) -> int:
            depth = 0
            i = offset
            while i < len(data):
                if data[i:i+1] == b'd' or data[i:i+1] == b'l':
                    depth += 1
                    i += 1
                elif data[i:i+1] == b'e':
                    depth -= 1
                    i += 1
                    if depth == 0:
                        return i
                elif data[i:i+1] == b'i':
                    # integer: i<number>e
                    end_i = data.find(b'e', i)
                    if end_i == -1:
                        raise ValueError("Malformed bencoded integer.")
                    i = end_i + 1
                elif data[i:i+1].isdigit():
                    # string: <len>:<data>
                    colon = data.find(b':', i)
                    if colon == -1:
                        raise ValueError("Malformed bencoded string.")
                    strlen = int(data[i:colon])
                    i = colon + 1 + strlen
                else:
                    raise ValueError("Malformed bencoded data.")
            raise ValueError("Could not find end of 'info' dictionary.")

        info_end = find_dict_end(torrent_content, info_start)
        return info_start, info_end

    def _extract_info_hash_from_torrent(torrent_content: bytes) -> str:
        """
        Extracts the info hash from binary torrent content.

        :param torrent_content: Binary content of a torrent file.
        :return: The info hash as a hexadecimal string.
        """
        if not isinstance(torrent_content, bytes):
            raise TypeError("argument must be of type 'bytes'.")
        try:
            # Decode the bencoded torrent content
            info_start, info_end = _get_info_section_from_torrent(torrent_content)
            info_content = torrent_content[info_start:info_end]

            # Hash the "info" dictionary using SHA-1
            digest: hashes.Hash = hashes.Hash(hashes.SHA1(), backend=default_backend())
            digest.update(info_content)
            info_hash: bytes = digest.finalize()
            return info_hash.hex()
        except Exception as e:
            raise ValueError(f"Failed to extract info hash: {e}")

    def _extract_info_hash_from_magnet(magnet_url: str) -> str:
        """
        Extracts the info hash from a magnet URL.

        :param magnet_url: A magnet URL string.
        :return: The info hash as a hexadecimal string.
        """
        BTV1_HASH_KEY: Final[str] = "urn:btih:"
        BTV2_HASH_KEY: Final[str] = "urn:btmh:"

        up = urllib.parse.urlparse(magnet_url)
        qs = urllib.parse.parse_qs(up.query)
        xts = qs.get("xt", [""])
        info_hash = None
        if up.scheme == "magnet":
            for xt in xts:
                if xt.startswith(BTV1_HASH_KEY):
                    xt = xt[len(BTV1_HASH_KEY):]
                    if len(xt) == 40:
                        info_hash = xt
                        break
                    elif len(xt) == 32:
                        info_hash = base64.b32decode(xt).hex()
                        break

                elif xt.startswith(BTV2_HASH_KEY):
                    xt = xt[len(BTV2_HASH_KEY):]
                    if len(xt) == 40:
                        info_hash = xt
                        break

        if info_hash is None:
            raise ValueError("Invalid magnet URL: Info hash not found.")

        return info_hash

    if isinstance(input_data, str):
        up = urllib.parse.urlparse(input_data)
        # Handle magnet URL
        if up.scheme == "magnet":
            return _extract_info_hash_from_magnet(input_data)

        else:
            # Handle torrent URL
            if up.scheme in ("http", "https") and up.path.endswith(".torrent"):
                return _extract_info_hash_from_torrent(get_url(input_data))

            else:
                raise ValueError("Invalid input URL: Info hash not found.")

    elif hasattr(input_data, 'read') and callable(getattr(input_data, 'read')) and hasattr(input_data, 'readable') and input_data.readable():
        # Handle file-like object
        return _extract_info_hash_from_torrent(input_data.read())

    elif isinstance(input_data, bytes):
        # Handle binary content
        return _extract_info_hash_from_torrent(input_data)

    else:
        raise TypeError("Unsupported input type. Must be a URL, file-like object, or binary content.")
