# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re
from pyload.Api import MediaType

filetypes = {
    MediaType.Audio: re.compile("\.(m3u|m4a|mp3|wav|wma|aac?|flac|midi|m4b)$", re.I),
    MediaType.Image: re.compile("\.(jpe?g|bmp|png|gif|ico|tiff?|svg|psd)$", re.I),
    MediaType.Video: re.compile("\.(3gp|flv|m4v|avi|mp4|mov|swf|vob|wmv|divx|mpe?g|rm|mkv)$", re.I),
    MediaType.Document: re.compile("\.(epub|mobi|acsm|azw[0-9]|pdf|txt|md|abw|docx?|tex|odt|rtf||log)$", re.I),
    MediaType.Archive: re.compile("\.(rar|r[0-9]+|7z|7z.[0-9]+|zip|gz|bzip2?|tar|lzma)$", re.I),
    MediaType.Executable: re.compile("\.(jar|exe|dmg|sh|apk)$", re.I),
}


def guess_type(name):
    for mt, regex in filetypes.items():
        if regex.search(name) is not None:
            return mt

    return MediaType.Other
