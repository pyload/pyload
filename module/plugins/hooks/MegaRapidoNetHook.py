# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class MegaRapidoNetHook(MultiHook):
    __name__    = "MegaRapidoNetHook"
    __type__    = "hook"
    __version__ = "0.03"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """MegaRapido.net hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def get_hosters(self):
        hosters = {'1fichier'    : [],  # leave it there are so many possible addresses?
                   '1st-files'   : ['1st-files.com'],
                   '2shared'     : ['2shared.com'],
                   '4shared'     : ['4shared.com', '4shared-china.com'],
                   'asfile'      : ['http://asfile.com/'],
                   'bitshare'    : ['bitshare.com'],
                   'brupload'    : ['brupload.net'],
                   'crocko'      : ['crocko.com', 'easy-share.com'],
                   'dailymotion' : ['dailymotion.com'],
                   'depfile'     : ['depfile.com'],
                   'depositfiles': ['depositfiles.com', 'dfiles.eu'],
                   'dizzcloud'   : ['dizzcloud.com'],
                   'dl.dropbox'  : [],
                   'extabit'     : ['extabit.com'],
                   'extmatrix'   : ['extmatrix.com'],
                   'facebook'    : [],
                   'file4go'     : ['file4go.com'],
                   'filecloud'   : ['filecloud.io', 'ifile.it', 'mihd.net'],
                   'filefactory' : ['filefactory.com'],
                   'fileom'      : ['fileom.com'],
                   'fileparadox' : ['fileparadox.in'],
                   'filepost'    : ['filepost.com', 'fp.io'],
                   'filerio'     : ['filerio.in', 'filerio.com', 'filekeen.com'],
                   'filesflash'  : ['filesflash.com'],
                   'firedrive'   : ['firedrive.com', 'putlocker.com'],
                   'flashx'      : [],
                   'freakshare'  : ['freakshare.net', 'freakshare.com'],
                   'gigasize'    : ['gigasize.com'],
                   'hipfile'     : ['hipfile.com'],
                   'junocloud'   : ['junocloud.me'],
                   'letitbit'    : ['letitbit.net', 'shareflare.net'],
                   'mediafire'   : ['mediafire.com'],
                   'mega'        : ['mega.co.nz'],
                   'megashares'  : ['megashares.com'],
                   'metacafe'    : ['metacafe.com'],
                   'netload'     : ['netload.in'],
                   'oboom'       : ['oboom.com'],
                   'rapidgator'  : ['rapidgator.net'],
                   'rapidshare'  : ['rapidshare.com'],
                   'rarefile'    : ['rarefile.net'],
                   'ryushare'    : ['ryushare.com'],
                   'sendspace'   : ['sendspace.com'],
                   'turbobit'    : ['turbobit.net', 'unextfiles.com'],
                   'uploadable'  : ['uploadable.ch'],
                   'uploadbaz'   : ['uploadbaz.com'],
                   'uploaded'    : ['uploaded.to', 'uploaded.net', 'ul.to'],
                   'uploadhero'  : ['uploadhero.com'],
                   'uploading'   : ['uploading.com'],
                   'uptobox'     : ['uptobox.com'],
                   'xvideos'     : ['xvideos.com'],
                   'youtube'     : ['youtube.com']}

        hoster_list = []

        for item in hosters.values():
            hoster_list.extend(item)

        return hoster_list
