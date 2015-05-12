# -*- coding: utf-8 -*-

import re
import urlparse


endings = ("jdeatme", "3gp", "7zip", "7z", "abr", "ac3", "aiff", "aifc", "aif", "ai",
           "au", "avi", "apk", "bin", "bmp", "bat", "bz2", "cbr", "cbz", "ccf", "chm",
           "cr2", "cso", "cue", "cvd", "dta", "deb", "divx", "djvu", "dlc", "dmg", "doc",
           "docx", "dot", "eps", "epub", "exe", "ff", "flv", "flac", "f4v", "gsd", "gif",
           "gpg", "gz", "iwd", "idx", "iso", "ipa", "ipsw", "java", "jar", "jpe?g", "load",
           "m2ts", "m4v", "m4a", "md5", "mkv", "mp2", "mp3", "mp4", "mobi", "mov", "movie",
           "mpeg", "mpe", "mpg", "mpq", "msi", "msu", "msp", "mv", "mws", "nfo", "npk", "oga",
           "ogg", "ogv", "otrkey", "par2", "pkg", "png", "pdf", "pptx?", "ppsx?", "ppz", "pot",
           "psd", "qt", "rmvb", "rm", "rar", "ram", "ra", "rev", "rnd", "rpm", "run", "rsdf",
           "reg", "rtf", "shnf", "sh(?!tml)", "ssa", "smi", "sub", "srt", "snd", "sfv", "sfx",
           "swf", "swc", "tar\.(gz|bz2|xz)", "tar", "tgz", "tiff?", "ts", "txt", "viv", "vivo",
           "vob", "vtt", "webm", "wav", "wmv", "wma", "xla", "xls", "xpi", "zeno", "zip",
           "[r-z]\d{2}", "_[_a-z]{2}", "\d{3,4}(?=\?|$|\"|\r|\n)")

rarPats = [re.compile(r'(.*)(\.|_|-)pa?r?t?\.?\d+.(rar|exe)$', re.I),
           re.compile(r'(.*)(\.|_|-)part\.?[0]*[1].(rar|exe)$', re.I),
           re.compile(r'(.*)\.rar$', re.I),
           re.compile(r'(.*)\.r\d+$', re.I),
           re.compile(r'(.*)(\.|_|-)\d+$', re.I)]

zipPats = [re.compile(r'(.*)\.zip$', re.I),
           re.compile(r'(.*)\.z\d+$', re.I),
           re.compile(r'(?is).*\.7z\.[\d]+$', re.I),
           re.compile(r'(.*)\.a.$', re.I)]

ffsjPats = [re.compile(r'(.*)\._((_[a-z])|([a-z]{2}))(\.|$)'),
            re.compile(r'(.*)(\.|_|-)[\d]+(\.(' + '|'.join(endings) + ')$)', re.I)]

iszPats = [re.compile(r'(.*)\.isz$', re.I),
           re.compile(r'(.*)\.i\d{2}$', re.I)]

pat0 = re.compile(r'www\d*\.', re.I)

pat1 = re.compile(r'(\.?CD\d+)', re.I)
pat2 = re.compile(r'(\.?part\d+)', re.I)

pat3 = re.compile(r'(.+)[\.\-_]+$')
pat4 = re.compile(r'(.+)\.\d+\.xtm$')


def matchFirst(string, *args):
    """ matches against list of regexp and returns first match """
    for patternlist in args:
        for pattern in patternlist:
            m = pattern.search(string)
            if m is not None:
                name = m.group(1)
                return name

    return string


def parseNames(files):
    """ Generates packages names from name, data lists

    :param files: list of (name, data)
    :return: packagenames mapped to data lists (eg. urls)
    """
    packs = {}

    for file, url in files:
        patternMatch = False

        if file is None:
            continue

        # remove trailing /
        name = file.rstrip('/')

        # extract last path part .. if there is a path
        split = name.rsplit("/", 1)
        if len(split) > 1:
            name = split.pop(1)

            # check if an already existing package may be ok for this file
        #        found = False
        #        for pack in packs:
        #            if pack in file:
        #                packs[pack].append(url)
        #                found = True
        #                break
        #
        #        if found:
        #            continue

        # unrar pattern, 7zip/zip and hjmerge pattern, isz pattern, FFSJ pattern
        before = name
        name = matchFirst(name, rarPats, zipPats, iszPats, ffsjPats)
        if before != name:
            patternMatch = True

        # xtremsplit pattern
        m = pat4.search(name)
        if m is not None:
            name = m.group(1)

        # remove part and cd pattern
        m = pat1.search(name)
        if m is not None:
            name = name.replace(m.group(0), "")
            patternMatch = True

        m = pat2.search(name)
        if m is not None:
            name = name.replace(m.group(0), "")
            patternMatch = True

        # additional checks if extension pattern matched
        if patternMatch:
            # remove extension
            index = name.rfind(".")
            if index <= 0:
                index = name.rfind("_")
            if index > 0:
                length = len(name) - index
                if length <= 4:
                    name = name[:-length]

            # remove endings like . _ -
            m = pat3.search(name)
            if m is not None:
                name = m.group(1)

            # replace . and _ with space
            name = name.replace(".", " ")
            name = name.replace("_", " ")

            name = name.strip()
        else:
            name = ""

        #@NOTE: fallback: package by hoster
        if not name:
            name = urlparse.urlparse(file).netloc
            if name:
                name = pat0.sub("", name)

        # fallback : default name
        if not name:
            name = _("Unnamed package")

        # build mapping
        if name in packs:
            packs[name].append(url)
        else:
            packs[name] = [url]

    return packs
