# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class ShareRapidComFolder(SimpleCrypter):
    __name__ = "ShareRapidComFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?((share(-?rapid\.(biz|com|cz|info|eu|net|org|pl|sk)|-(central|credit|free|net)\.cz|-ms\.net)|(s-?rapid|rapids)\.(cz|sk))|(e-stahuj|mediatack|premium-rapidshare|rapidshare-premium|qiuck)\.cz|kadzet\.com|stahuj-zdarma\.eu|strelci\.net|universal-share\.com)/(slozka/.+)'

    __description__ = """Share-Rapid.com folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    LINK_PATTERN = r'<td class="soubor"[^>]*><a href="([^"]+)">'
