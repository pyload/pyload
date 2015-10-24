# -*- coding: utf-8 -*-
#
#@TODO: Move to utils directory 0.4.10

import datetime
import htmlentitydefs
import itertools
import os
import re
import string
import sys
import time
import traceback
import urllib
import urlparse

try:
    import HTMLParser

except ImportError:  #@TODO: Remove in 0.4.10
    import xml.sax.saxutils

try:
    import simplejson as json

except ImportError:
    import json


class utils(object):
    __name__    = "utils"
    __type__    = "plugin"
    __version__ = "0.08"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = []

    __description__ = """Dummy utils class"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


def lock(fn):
    def new(*args):
        # print "Handler: %s args: %s" % (fn, args[1:])
        args[0].lock.acquire()
        try:
            return fn(*args)

        finally:
            args[0].lock.release()

    return new


def format_time(value):
    dt   = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=abs(int(value)))
    days = ("%d days and " % (dt.day - 1)) if dt.day > 1 else ""
    return days + ", ".join("%d %ss" % (getattr(dt, attr), attr) for attr in ("hour", "minute", "second")
                            if getattr(dt, attr))


def format_size(value):
    size  = int(value)
    steps = 0
    sizes = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB')
    while size > 1000:
        size /= 1024.0
        steps += 1
    return "%.2f %s" % (size, sizes[steps])


def compare_time(start, end):
    start = map(int, start)
    end   = map(int, end)

    if start == end:
        return True

    now = list(time.localtime()[3:5])

    if start < end:
        if now < end:
            return True

    elif now > start or now < end:
            return True

    return False


def uniqify(seq):
    """
    Remove duplicates from list preserving order
    Originally by Dave Kirby
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def has_method(obj, name):
    """
    Check if name was defined in obj (return false if inhereted)
    """
    return hasattr(obj, '__dict__') and name in obj.__dict__


def html_unescape(text):
    """
    Removes HTML or XML character references and entities from a text string
    """
    try:
        h = HTMLParser.HTMLParser()
        return h.unescape(text)

    except NameError:  #@TODO: Remove in 0.4.10
        return xml.sax.saxutils.unescape(text)


def isiterable(obj):
    return hasattr(obj, "__iter__")


def get_console_encoding(enc):
    if os.name is "nt":
        if enc is "cp65001":  #: aka UTF-8
            enc = "cp850"
            print "WARNING: Windows codepage 65001 (UTF-8) is not supported, used `%s` instead" % enc
    else:
        enc = "utf8"

    return enc


#@NOTE: Revert to `decode` in Python 3
def decode(value, encoding=None):
    """
    Encoded string (default to UTF-8) -> unicode string
    """
    if type(value) is str:
        try:
            # res = value.decode(encoding or 'utf-8')
            res = unicode(value, encoding or 'utf-8')

        except UnicodeDecodeError, e:
            if encoding:
                raise UnicodeDecodeError(e)

            encoding = get_console_encoding(sys.stdout.encoding)
            # res = value.decode(encoding)
            res = unicode(value, encoding)

    elif type(value) is unicode:
        res = value

    else:
        res = unicode(value)

    return res


def encode(value, encoding=None, decoding=None):
    """
    Unicode or decoded string -> encoded string (default to UTF-8)
    """
    if type(value) is unicode:
        res = value.encode(encoding or "utf-8")

    # elif type(value) is str:
        # res = encode(decode(value, decoding), encoding)

    else:
        res = str(value)

    return res


def fs_join(*args):
    """
    Like os.path.join, but encoding aware
    """
    return os.path.join(*map(encode, args))


def exists(path):
    if os.path.exists(path):
        if os.name is "nt":
            dir, name = os.path.split(path.rstrip(os.sep))
            return name in os.listdir(dir)
        else:
            return True
    else:
        return False


def remove_chars(value, repl):
    """
    Remove all chars in repl from string
    """
    if type(repl) is unicode:
        for badc in list(repl):
            value = value.replace(badc, "")
        return value

    elif type(value) is unicode:
        return value.translate(dict((ord(s), None) for s in repl))

    elif type(value) is str:
        return value.translate(string.maketrans("", ""), repl)


def fixurl(url, unquote=None):
    old = url
    url = urllib.unquote(url)

    if unquote is None:
        unquote = url is old

    url = html_unescape(decode(url).decode('unicode-escape'))
    url = re.sub(r'(?<!:)/{2,}', '/', url).strip().lstrip('.')

    if not unquote:
        url = urllib.quote(url)

    return url


def fixname(value):
    repl = '<>:"/\\|?*' if os.name is "nt" else '\0/\\"'
    return remove_chars(value, repl)


def parse_name(value, safechar=True):
    path  = fixurl(decode(value), unquote=False)
    url_p = urlparse.urlparse(path.rstrip('/'))
    name  = (url_p.path.split('/')[-1] or
              url_p.query.split('=', 1)[::-1][0].split('&', 1)[0] or
              url_p.netloc.split('.', 1)[0])

    name = urllib.unquote(name)
    return fixname(name) if safechar else name


def parse_size(value, unit=""):  #: returns bytes
    m = re.match(r"([\d.,]+)\s*([\w^_]*)", str(value).lower())

    if m is None:
        return 0

    traffic = float(m.group(1).replace(',', '.'))
    unit    = (unit.strip().lower() or m.group(2) or "byte")[0]

    if unit is "b":
        return int(traffic)

    sizes   = ['b', 'k', 'm', 'g', 't', 'p', 'e']
    sizemap = dict((u, i * 10) for i, u in enumerate(sizes))

    increment = sizemap[unit]
    integer, decimal = map(int, ("%.3f" % traffic).split('.'))

    return (integer << increment) + (decimal << increment - 10)


def str2int(value):
    try:
        return int(value)
    except:
        pass

    ones = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen")
    tens = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
            "eighty", "ninety")

    o_tuple = [(w, i) for i, w in enumerate(ones)]
    t_tuple = [(w, i * 10) for i, w in enumerate(tens)]

    numwords = dict(o_tuple + t_tuple)
    tokens   = re.split(r"[\s\-]+", value.lower())

    try:
        return sum(numwords[word] for word in tokens)
    except:
        return 0


def parse_time(value):
    if re.search("da(il)?y|today", value):
        seconds = seconds_to_midnight()

    else:
        regex   = re.compile(r'(\d+| (?:this|an?) )\s*(hr|hour|min|sec|)', re.I)
        seconds = sum((int(v) if v.strip() not in ("this", "a", "an") else 1) *
                      {'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1, '': 1}[u.lower()]
                      for v, u in regex.findall(value))
    return seconds


def timestamp():
    return int(time.time() * 1000)


def which(program):
    """
    Works exactly like the unix command which
    Courtesy of http://stackoverflow.com/a/377028/675646
    """
    isExe = lambda x: os.path.isfile(x) and os.access(x, os.X_OK)

    fpath, fname = os.path.split(program)

    if fpath:
        if isExe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path.strip('"'), program)
            if isExe(exe_file):
                return exe_file


def format_exc(frame=None):
    """
    Format call-stack and display exception information (if availible)
    """
    exception_info = sys.exc_info()
    callstack_list = traceback.extract_stack(frame)
    callstack_list = callstack_list[:-1]

    exception_desc = ""
    if exception_info[0] is not None:
        exception_callstack_list = traceback.extract_tb(exception_info[2])
        if callstack_list[-1][0] == exception_callstack_list[0][0]:  #Does this exception belongs to us?
            callstack_list = callstack_list[:-1]
            callstack_list.extend(exception_callstack_list)
            exception_desc = "".join(traceback.format_exception_only(exception_info[0], exception_info[1]))

    traceback_str  = "Traceback (most recent call last):\n"
    traceback_str += "".join(traceback.format_list(callstack_list))
    traceback_str += exception_desc

    return traceback_str


def seconds_to_nexthour(strict=False):
    now      = datetime.datetime.today()
    nexthour = now.replace(minute=0 if strict else 1, second=0, microsecond=0) + datetime.timedelta(hours=1)
    return (nexthour - now).seconds


def seconds_to_midnight(utc=None, strict=False):
    if utc is None:
        now = datetime.datetime.today()
    else:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=utc)

    midnight = now.replace(hour=0, minute=0 if strict else 1, second=0, microsecond=0) + datetime.timedelta(days=1)

    return (midnight - now).seconds


def replace_patterns(value, rules):
    for r in rules:
        try:
            pattern, repl, flags = r

        except ValueError:
            pattern, repl = r
            flags = 0

        value = re.sub(pattern, repl, value, flags)

    return value


#@TODO: Remove in 0.4.10 and fix exp in CookieJar.setCookie
def set_cookie(cj, domain, name, value, path='/', exp=time.time() + 180 * 24 * 3600):
    return cj.setCookie(encode(domain), encode(name), encode(value), encode(path), int(exp))


def set_cookies(cj, cookies):
    for cookie in cookies:
        if isinstance(cookie, tuple) and len(cookie) == 3:
            set_cookie(cj, *cookie)


def parse_html_tag_attr_value(attr_name, tag):
    m = re.search(r"%s\s*=\s*([\"']?)((?<=\")[^\"]+|(?<=')[^']+|[^>\s\"'][^>\s]*)\1" % attr_name, tag, re.I)
    return m.group(2) if m else None


def parse_html_form(attr_str, html, input_names={}):
    for form in re.finditer(r"(?P<TAG><form[^>]*%s[^>]*>)(?P<CONTENT>.*?)</?(form|body|html)[^>]*>" % attr_str,
                            html, re.I | re.S):
        inputs = {}
        action = parse_html_tag_attr_value("action", form.group('TAG'))

        for inputtag in re.finditer(r'(<(input|textarea)[^>]*>)([^<]*(?=</\2)|)', form.group('CONTENT'), re.I | re.S):
            name = parse_html_tag_attr_value("name", inputtag.group(1))
            if name:
                value = parse_html_tag_attr_value("value", inputtag.group(1))
                if not value:
                    inputs[name] = inputtag.group(3) or ""
                else:
                    inputs[name] = value

        if not input_names:
            #: No attribute check
            return action, inputs
        else:
            #: Check input attributes
            for key, val in input_names.items():
                if key in inputs:
                    if isinstance(val, basestring) and inputs[key] is val:
                        continue
                    elif isinstance(val, tuple) and inputs[key] in val:
                        continue
                    elif hasattr(val, "search") and re.match(val, inputs[key]):
                        continue
                    else:
                        break  #: Attibute value does not match
                else:
                    break  #: Attibute name does not match
            else:
                return action, inputs  #: Passed attribute check

    return {}, None  #: No matching form found


def chunks(iterable, size):
    it   = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))


def renice(pid, value):
    if not value or os.name is "nt":
        return

    try:
        subprocess.Popen(["renice", str(value), str(pid)],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         bufsize=-1)
    except Exception:
        pass
