# -*- coding: utf-8 -*-

""" Store all usefull functions here """

import os
import time
import re
from string import maketrans
from itertools import islice
from htmlentitydefs import name2codepoint

def decode(string):
    """ decode string with utf if possible """
    try:
        if type(string) == str:
            return string.decode("utf8", "replace")
        else:
            return string
    except:
        return string

def encode(string):
    """ decode string to utf if possible """
    try:
        if type(string) == unicode:
            return string.encode("utf8", "replace")
        else:
            return string
    except:
        return string

def remove_chars(string, repl):
    """ removes all chars in repl from string"""
    if type(string) == str:
        return string.translate(maketrans("", ""), repl)
    elif type(string) == unicode:
        return string.translate(dict([(ord(s), None) for s in repl]))


def get_console_encoding(enc):
    if os.name == "nt": 
        if enc == "cp65001": # aka UTF-8
            print "WARNING: Windows codepage 65001 is not supported."
            enc = "cp850"
    else:
        enc = "utf8"
    
    return enc

def compare_time(start, end):
    start = map(int, start)
    end = map(int, end)

    if start == end: return True

    now = list(time.localtime()[3:5])
    if start < now < end: return True
    elif start > end and (now > start or now < end): return True
    elif start < now > end < start: return True
    else: return False

def to_list(value):
    return value if type(value) == list else ([value] if value is not None else [])

def formatSize(size):
    print "Deprecated formatSize, use format_size"
    return format_size(size)

def format_size(bytes):
    bytes = int(bytes)
    steps = 0
    sizes = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    while bytes > 1000:
        bytes /= 1024.0
        steps += 1
    return "%.2f %s" % (bytes, sizes[steps])

def formatSpeed(speed):
    print "Deprecated formatSpeed, use format_speed"
    return format_speed(speed)

def format_speed(speed):
    return format_size(speed) + "/s"

def format_time(seconds):
    if seconds < 0: return "00:00:00"
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)

def uniqify(seq): #by Dave Kirby
    """ removes duplicates from list, preserve order """
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def bits_set(bits, compare):
    """ checks if all bits are set in compare, or bits is 0 """
    return bits == (bits & compare)

def parseFileSize(string, unit=None): #returns bytes
    if not unit:
        m = re.match(r"(\d*[\.,]?\d+)(.*)", string.strip().lower())
        if m:
            traffic = float(m.group(1).replace(",", "."))
            unit = m.group(2)
        else:
            return 0
    else:
        if isinstance(string, basestring):
            traffic = float(string.replace(",", "."))
        else:
            traffic = string

    #ignore case
    unit = unit.lower().strip()

    if unit in ("gb", "gig", "gbyte", "gigabyte", "gib", "g"):
        traffic *= 1 << 30
    elif unit in ("mb", "mbyte", "megabyte", "mib", "m"):
        traffic *= 1 << 20
    elif unit in ("kb", "kib", "kilobyte", "kbyte", "k"):
        traffic *= 1 << 10

    return traffic


def lock(func):
    def new(*args):
        #print "Handler: %s args: %s" % (func,args[1:])
        args[0].lock.acquire()
        try:
            return func(*args)
        finally:
            args[0].lock.release()

    return new

def chunks(iterable, size):
    it = iter(iterable)
    item = list(islice(it, size))
    while item:
        yield item
        item = list(islice(it, size))


def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
        # character reference
        try:
            if text[:3] == "&#x":
                return unichr(int(text[3:-1], 16))
            else:
                return unichr(int(text[2:-1]))
        except ValueError:
            pass
    else:
        # named entity
        try:
            name = text[1:-1]
            text = unichr(name2codepoint[name])
        except KeyError:
            pass

    return text # leave as is


def has_method(obj, name):
    """ checks if 'name' was defined in obj, (false if it was inhereted) """
    return name in obj.__dict__

def accumulate(it, inv_map=None):
    """ accumulate (key, value) data to {value : [keylist]} dictionary """
    if not inv_map:
        inv_map = {}

    for key, value in it:
        if value in inv_map:
            inv_map[value].append(key)
        else:
            inv_map[value] = [key]

    return inv_map

def to_string(value):
    return str(value) if not isinstance(value, basestring) else value

def to_int(string, default=0):
    """ return int from string or default """
    try:
        return int(string)
    except ValueError:
        return default

def from_string(value, typ=None):
    """ cast value to given type, unicode for strings """

    # value is no string
    if not isinstance(value, basestring):
        return value

    value = decode(value)

    if typ == "int":
        return int(value)
    elif typ == "bool":
        return True if value.lower() in ("1", "true", "on", "an", "yes") else False
    elif typ == "time":
        if not value: value = "0:00"
        if not ":" in value: value += ":00"
        return value
    else:
        return value

def get_index(l, value):
    """ .index method that also works on tuple and python 2.5 """
    for pos, t in enumerate(l):
        if t == value:
            return pos

    # Matches behavior of list.index
    raise ValueError("list.index(x): x not in list")

def primary_uid(user):
    """ Gets primary user id for user instances or ints """
    if type(user) == int: return user
    return user.primary if user else None

def html_unescape(text):
    """Removes HTML or XML character references and entities from a text string"""
    return re.sub("&#?\w+;", fixup, text)

if __name__ == "__main__":
    print remove_chars("ab'cdgdsf''ds'", "'ghd")
