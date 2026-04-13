
# import hashlib
# import mimetypes
import re
import urllib.parse
from email.header import decode_header as parse_mime_header
from ntpath import basename as ntpath_basename
from posixpath import basename as posixpath_basename

from ..parse import name as parse_name
from ..purge import name as safe_nm
from . import format, purge

# import tld
# from ..check import isiterable



# from .check import is_host, is_port
# from .convert import host_to_ip, ip_to_host, splitaddress


# def socket(text):
#     addr, port = splitaddress(text.strip())
#     ip = addr if isip(addr) else host_to_ip(addr)
#     if port is not None and not is_port(port):
#         raise ValueError(port)
#     return ip, port


# def endpoint(text):
#     addr, port = splitaddress(text.strip())
#     host = addr if is_host(addr) else ip_to_host(addr)
#     if port is not None and not is_port(port):
#         raise ValueError(port)
#     return host, port


# TODO: Recheck result format
# def attr(text, name=None):
#     pattr = r'{}\s*=\s*(["\']?)((?<=")[^"]+|(?<=\')[^\']+|[^>\s"\'][^>\s]*)\1'
#     pattr = pattr.format(name or r"\w+")
#     m = re.search(pattr, text, flags=re.I)
#     return m.group(2) if m is not None else None


# def domain(url):
#     return tld.get_tld(format.url(url), fail_silently=True)


# _RE_FORM = re.compile(r"(<(input|textarea).*?>)([^<]*(?=</\2)|)", flags=re.I | re.S)

# def _extract_inputs(form):
#     taginputs = {}
#     for inputtag in _RE_FORM.finditer(purge.comments(form.group("CONTENT"))):
#         tagname = attr(inputtag.group(1), "name")
#         if not tagname:
#             continue
#         tagvalue = attr(inputtag.group(1), "value")
#         taginputs[tagname] = tagvalue or inputtag.group(3) or ""
#     return taginputs


# def _same_inputs(taginputs, inputs):
#     for key, value in inputs.items():
#         if key not in taginputs:
#             return False
#         tagvalue = taginputs[key]
#         if hasattr(value, "search") and re.match(value, tagvalue):
#             continue
#         elif isiterable(value) and tagvalue in value:
#             continue
#         elif tagvalue == value:
#             continue
#         return False
#     return True


# def form(text, name=None, inputs=None):
#     pattr = r"(?P<TAG><form[^>]*{}.*?>)(?P<CONTENT>.*?)</?(form|body|html).*?>"
#     pattr = pattr.format(name or "")
#     for form in re.finditer(pattr, text, flags=re.I | re.S):
#         taginputs = _extract_inputs(form)
#         formaction = attr(form.group("TAG"), "action")
#         # Check input attributes
#         if not inputs or _same_inputs(taginputs, inputs):
#             return formaction, taginputs  # Passed attribute check
#     return None, {}  # No matching form found


# def hash(text):
#     text = text.replace("-", "").lower()
#     algop = "|".join(hashlib.algorithms_available + ("adler32", "crc(32)?"))
#     pattr = rf"(?P<D1>{algop}|)\s*[:=]?\s*(?P<H>[\w^_]{8,}?)\s*[:=]?\s*(?P<D2>{algop}|)"
#     m = re.search(pattr, text)
#     if m is None:
#         return None, None

#     checksum = m.group("H")
#     algorithm = m.group("D1") or m.group("D2")
#     if algorithm == "crc":
#         algorithm = "crc32"

#     return checksum, algorithm


# def mime(text, strict=False):
#     DEFAULT_MIMETYPE = "application/octet-stream"
#     mimetype = mimetypes.guess_type(text.strip(), strict)[0]
#     return mimetype or DEFAULT_MIMETYPE


def name(url, safe_name=True):
    url = format.url(url)
    us = urllib.parse.urlsplit(url)
    name = us.path.split("/")[-1]
    if not name:
        name = us.query.split("=", 1)[::-1][0].split("&", 1)[0]
    if not name:
        name = ".".join(us.netloc.split(".")[:-1])

    return safe_nm(name) if safe_name else name


def http_header(line):
    """
    Parse a Content-type like http header.

    :param line:
    :Return: the main content-type and a dictionary of options.
    """
    def _parseparam(s):
        while s[:1] == ';':
            s = s[1:]
            end = s.find(';')
            while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
                end = s.find(';', end + 1)
            if end < 0:
                end = len(s)
            f = s[:end]
            yield f.strip()
            s = s[end:]

    parts = _parseparam(';' + line)
    key = parts.__next__()
    pdict = {}
    for p in parts:
        i = p.find('=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i+1:].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace('\\\\', '\\').replace('\\"', '"')
            pdict[name] = value
    return key, pdict


def disposition(disposition_value, location=None, fallback_url=None):
    """
    Extract and sanitize filename from a Content-Disposition header value.
    """
    def _extract_filename_star(_disposition_params):
        """Extract filename from filename* parameter (RFC 5987)."""
        if 'filename*' not in _disposition_params:
            return None

        _filename = _disposition_params['filename*']

        # Try RFC 2047 encoding
        m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', _filename, re.I)
        if m is not None:
            try:
                data, encoding = parse_mime_header(_filename)[0]
                return data.decode(encoding)
            except (LookupError, UnicodeEncodeError) as exc:
                raise ValueError(f"Content-Disposition: | error: {exc}")

        # Try RFC 5987 encoding
        m = re.search(r'(.+?)\'(.*)\'(.+)', _filename)
        if m is not None:
            encoding, lang, data = m.groups()
            try:
                return urllib.parse.unquote(data, encoding=encoding, errors="strict")
            except (LookupError, UnicodeDecodeError) as exc:
                raise ValueError(f"Content-Disposition: | error: {exc}")

        return None

    def _extract_filename(_disposition_params):
        """Extract filename from filename parameter."""
        if 'filename' not in _disposition_params:
            return None

        _filename = _disposition_params['filename']

        # Try RFC 2047 encoding
        m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', _filename, re.I)
        if m is not None:
            try:
                data, encoding = parse_mime_header(m.group(0))[0]
                return data.decode(encoding)
            except (LookupError, UnicodeEncodeError) as exc:
                raise ValueError(f"Content-Disposition: | error: {exc}")

        # Try URL decoding
        try:
            return urllib.parse.unquote(_filename, encoding="iso-8859-1", errors="strict")
        except UnicodeDecodeError:
            raise ValueError("Content-Disposition: | error: Error when decoding string from iso-8859-1.")

    def _extract_attachment_filename(_disposition_type, _location, _fallback_url):
        """Extract filename for attachment disposition type."""
        if _disposition_type.lower() != "attachment":
            return None

        if _location is not None:
            return parse_name(_location)
        elif _fallback_url is not None:
            return parse_name(_fallback_url)

        return None

    def _sanitize_filename(_filename):
        """Drop unsafe characters from filename."""
        _filename = posixpath_basename(_filename)
        _filename = ntpath_basename(_filename)
        _filename = safe_nm(_filename)
        _filename = _filename.lstrip('.')

        return _filename

    disposition_type, disposition_params = http_header(disposition_value)
    filename = (
        _extract_filename_star(disposition_params) or
        _extract_filename(disposition_params) or
        _extract_attachment_filename(disposition_type, location, fallback_url)
    )

    if filename:
        return _sanitize_filename(filename)

    return None
