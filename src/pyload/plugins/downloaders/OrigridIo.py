# pyLoad hoster plugin for Origrid (https://origrid.io)
#
# Origrid serves everything a downloader needs from plain HTML: no captcha, no
# wait timer, no account, no anti-bot wall. Name, size and the direct link are
# all in the server-rendered page, so this plugin needs no JS unpacking — unlike
# most hosts, where half the plugin is undoing someone's obfuscation.
#
# The `data-origrid="…"` attributes the patterns below key on are a deliberate,
# documented contract on Origrid's side (see the note at the top of
# src/routes/d/[id]/+page.svelte). They exist precisely so this plugin doesn't
# depend on CSS class names, which carry a build hash and change on every deploy.

import re

from ..base.simple_downloader import SimpleDownloader


class OrigridIo(SimpleDownloader):
    __name__ = "OrigridIo"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?origrid\.io/d/(?P<ID>[\w\-]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Origrid.io downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Origrid", "admin@origrid.io")]

    # Name and size come from stable data-origrid anchors, not from CSS classes.
    NAME_PATTERN = r'data-origrid="name"[^>]*>(?P<N>[^<]+)<'
    SIZE_PATTERN = r'data-origrid-bytes="(?P<S>\d+)"'
    # Two distinct dead-link states, and the page distinguishes them:
    #   - unknown id     -> "This link doesn't lead to a file"
    #   - expired file   -> banner carrying data-origrid="offline"
    # The anchor comes first because it is the stable one: the visible copy is
    # translated and rewritten, the attribute is not.
    # The expired case was missing until 2026-09-07. Without it the link matched
    # neither online nor offline, so pyLoad treated it as a temporary error and
    # retried in a loop instead of marking it dead.
    OFFLINE_PATTERN = (
        r'data-origrid="offline"'
        r"|This link doesn&#39;t lead to a file|This link doesn't lead to a file"
    )

    # The download anchor is present in the server HTML (no JS needed). The token
    # is single-use-ish and short-lived, so it is read per request rather than cached.
    LINK_FREE_PATTERN = r'data-origrid="download"[^>]*href="(?P<L>/dl/[^"]+)"'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://origrid.io/d/\g<ID>")]

    def setup(self):
        # Origrid sets no cap on concurrent downloads and redirects (302) to
        # storage with Accept-Ranges, so resuming and chunking are both safe.
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = -1

    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(self._("Download link not found"))

        link = m.group("L")
        if link.startswith("/"):
            link = "https://origrid.io" + link
        self.link = link
