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
    return value if type(value) == list else [value]

def formatSize(size):
    """formats size of bytes"""
    size = int(size)
    steps = 0
    sizes = ["B", "KiB", "MiB", "GiB", "TiB"]
    while size > 1000:
        size /= 1024.0
        steps += 1
    return "%.2f %s" % (size, sizes[steps])


def formatSpeed(speed):
    return formatSize(speed) + "/s"


def freeSpace(folder):
    print "Deprecated freeSpace"
    return free_space(folder)


def uniqify(seq, idfun=None):
# order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


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


def html_unescape(text):
    """Removes HTML or XML character references and entities from a text string"""
    return re.sub("&#?\w+;", fixup, text)

if __name__ == "__main__":
    print freeSpace(".")

    print remove_chars("ab'cdgdsf''ds'", "'ghd")


# TODO: Legacy import
from fs import chmod, save_path, save_join, fs_decode, fs_encode, free_space