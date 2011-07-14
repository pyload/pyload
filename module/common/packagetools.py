#!/usr/bin/env python

# JDownloader/src/jd/controlling/LinkGrabberPackager.java

import re
from urlparse import urlparse

def parseNames(files):
    packs = {}

    endings = "\\.(3gp|7zip|7z|abr|ac3|aiff|aifc|aif|ai|au|avi|bin|bz2|cbr|cbz|ccf|cue|cvd|chm|dta|deb|divx|djvu|dlc|dmg|doc|docx|dot|eps|exe|ff|flv|f4v|gsd|gif|gz|iwd|iso|ipsw|java|jar|jpg|jpeg|jdeatme|load|mws|mw|m4v|m4a|mkv|mp2|mp3|mp4|mov|movie|mpeg|mpe|mpg|msi|msu|msp|nfo|npk|oga|ogg|ogv|otrkey|pkg|png|pdf|pptx|ppt|pps|ppz|pot|psd|qt|rmvb|rm|rar|ram|ra|rev|rnd|r\\d+|rpm|run|rsdf|rtf|sh(!?tml)|srt|snd|sfv|swf|tar|tif|tiff|ts|txt|viv|vivo|vob|wav|wmv|xla|xls|xpi|zeno|zip|z\\d+|_[_a-z]{2}|\\d+$)"

    pat0 = re.compile("(.*)(\\.|_|-)pa?r?t?\\.?[0-9]+.(rar|exe)$", re.I)
    pat1 = re.compile("(.*)(\\.|_|-)part\\.?[0]*[1].(rar|exe)$", re.I)
    pat3 = re.compile("(.*)\\.rar$", re.I)
    pat4 = re.compile("(.*)\\.r\\d+$", re.I)
    pat5 = re.compile("(.*)(\\.|_|-)\\d+$", re.I)
    rarPats = [ pat0, pat1, pat3, pat4, pat5 ]

    pat6 = re.compile("(.*)\\.zip$", re.I)
    pat7 = re.compile("(.*)\\.z\\d+$", re.I)
    pat8 = re.compile("(?is).*\\.7z\\.[\\d]+$", re.I)
    pat9 = re.compile("(.*)\\.a.$", re.I)
    zipPats = [ pat6, pat7, pat8, pat9 ]

    pat10 = re.compile("(.*)\\._((_[a-z])|([a-z]{2}))(\\.|$)")
    pat11 = re.compile("(.*)(\\.|_|-)[\\d]+(" + endings + "$)", re.I)
    ffsjPats = [ pat10, pat11 ]

    pat12 = re.compile("(\\.?CD\\d+)", re.I)
    pat13 = re.compile("(\\.?part\\d+)", re.I)

    pat14 = re.compile("(.+)[\\.\\-_]+$")

    pat17 = re.compile("(.+)\\.\\d+\\.xtm$")

    pat18 = re.compile("(.*)\\.isz$", re.I)
    pat19 = re.compile("(.*)\\.i\\d{2}$", re.I)
    iszPats = [ pat18, pat19 ]

    for file in files:
        #check if a already existing package may be ok for this file
        found = False
        for name in packs:
            if name in file:
                packs[name].append(file)
                found = True
                break

        if found: continue

        # remove trailing /
        name = file.rstrip('/')

        # extract last path part .. if there is a path
        split = name.rsplit("/", 1)
        if len(split) > 1:
            name = split.pop(1)

        # unrar pattern
        for pattern in rarPats:
            r = pattern.search(name)
            if r is not None:
                name = r.group(1)
                break

        # 7zip/zip and hjmerge pattern
        for pattern in zipPats:
            r = pattern.search(name)
            if r is not None:
                name = r.group(1)
                break

        # isz pattern
        for pattern in iszPats:
            r = pattern.search(name)
            if r is not None:
                name = r.group(1)
                break

        # xtremsplit pattern
        r = pat17.search(name)
        if r is not None:
            name = r.group(1)

        # FFSJ pattern
        for pattern in ffsjPats:
            r = pattern.search(name)
            if r is not None:
                name = r.group(1)
                break

        # remove part and cd pattern
        r = pat12.search(name)
        if r is not None:
            name = name.replace(r.group(0), "")

        r = pat13.search(name)
        if r is not None:
            name = name.replace(r.group(0), "")

        # remove extension
        index = name.rfind(".")
        if index <= 0:
            index = name.rfind("_")
        if index > 0:
            length = len(name) - index
            if length <= 4:
                name = name[:-length]

        # remove endings like . _ -
        r = pat14.search(name)
        if r is not None:
            name = r.group(1)

        # replace . and _ with space
        name = name.replace(".", " ")
        name = name.replace("_", " ")

        name = name.strip()

        # checks if name could be a hash
        if file.find("file/"+name) >= 0:
            name = ""

        if file.find("files/"+name) >= 0:
            name = ""

        r = re.search("^[0-9]+$", name, re.I)
        if r is not None:
            name = ""

        r = re.search("^[0-9a-z]+$", name, re.I)
        if r is not None:
            r1 = re.search("[0-9]+.+[0-9]", name)
            r2 = re.search("[a-z]+.+[a-z]+", name, re.I)
            if r1 is not None and r2 is not None:
                name = ""

        # fallback: package by hoster
        if not len(name):
            name = urlparse(file).hostname

        # fallback : default name
        if not name:
            name = "unknown"

        # build mapping
        if name in packs:
            packs[name].append(file)
        else:
            packs[name] = [file]
            
    return packs