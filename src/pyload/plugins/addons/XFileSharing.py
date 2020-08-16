# -*- coding: utf-8 -*-
import inspect
import re

from ..base.addon import BaseAddon


class XFileSharing(BaseAddon):
    __name__ = "XFileSharing"
    __type__ = "addon"
    __version__ = "0.56"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("use_downloader_list", "bool", "Load listed hosters only", False),
        ("use_decrypter_list", "bool", "Load listed crypters only", False),
        ("use_builtin_list", "bool", "Load built-in plugin list", True),
        ("hoster_list", "str", "Hoster list (comma separated)", ""),
        ("crypter_list", "str", "Crypter list (comma separated)", ""),
    ]

    __description__ = (
        """Load XFileSharing hosters and crypters which don't need a own plugin"""
    )
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    _regexmap = {
        "downloader": (
            r"(?:https?://(?:www\.)?)(?!(?:www\.)?(?:{}))(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{{3,63}}(?:\.[a-zA-Z]{{2,}})+)(?:\:\d+)?)/(?:embed-)?\w{{12}}(?:\W|$)",
            r"https?://(?:[^/]+\.)?(?P<DOMAIN>{})/(?:embed-)?\w+",
        ),
        "decrypter": (
            r"(?:https?://(?:www\.)?)(?!(?:www\.)?(?:{}))(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{{3,63}}(?:\.[a-zA-Z]{{2,}})+)(?:\:\d+)?)/(?:user|folder)s?/\w+",
            r"https?://(?:[^/]+\.)?(?P<DOMAIN>{})/(?:user|folder)s?/\w+",
        ),
    }

    BUILTIN_HOSTERS = [  #: WORKING HOSTERS:
        "ani-stream.com",
        "backin.net",
        "cloudshares.net",
        "cloudsix.me",
        "eyesfile.ca",
        "file4safe.com",
        "fileband.com",
        "filedwon.com",
        "fileparadox.in",
        "filevice.com",
        "hostingbulk.com",
        "junkyvideo.com",
        "ravishare.com",
        "salefiles.com",
        "sendmyway.com",
        "sharebeast.com",
        "sharesix.com",
        "thefile.me",
        "verzend.be",
        "worldbytez.com",
        "xvidstage.com",
        # NOT TESTED:
        "101shared.com",
        "4upfiles.com",
        "filemaze.ws",
        "filenuke.com",
        "linkzhost.com",
        "mightyupload.com",
        "rockdizfile.com",
        "sharerepo.com",
        "shareswift.com",
        "uploadbaz.com",
        "uploadc.com",
        "vidbull.com",
        "zalaa.com",
        "zomgupload.com",
        # NOT WORKING:
        "amonshare.com",
        "banicrazy.info",
        "boosterking.com",
        "host4desi.com",
        "laoupload.com",
        "rd-fs.com",
    ]
    BUILTIN_CRYPTERS = ["junocloud.me", "rapidfileshare.net"]

    def activate(self):
        for type, plugin in (
            ("downloader", "XFileSharing"),
            ("decrypter", "XFileSharingFolder"),
        ):
            self._load(type, plugin)

    def deactivate(self):
        for type, plugin in (
            ("downloader", "XFileSharing"),
            ("decrypter", "XFileSharingFolder"),
        ):
            self._unload(type, plugin)

    def get_pattern(self, type, plugin):
        if self.config.get("use_{}_list".format(type)):
            plugin_list = self.config.get("{}_list".format(type))
            plugin_list = plugin_list.replace(" ", "").replace("\\", "")
            plugin_list = plugin_list.replace("|", ",").replace(";", ",")
            plugin_list = plugin_list.lower().split(",")

            plugin_set = set(plugin_list)

            if self.config.get("use_builtin_list"):
                builtin_list = getattr(self, "BUILTIN_{}S".format(type.upper()))
                plugin_set.update(builtin_list)

            plugin_set.difference_update(("", ""))

            if not plugin_set:
                self.log_info(self._("No {} to handle").format(type))
                return

            match_list = "|".join(sorted(plugin_set)).replace(".", r"\.")
            pattern = self._regexmap[type][1].format(match_list)

            self.log_info(
                self._("Handle {} {}{}: {}").format(
                    len(plugin_set),
                    type,
                    "" if len(plugin_set) == 1 else "s",
                    match_list.replace(r"\.", ".").replace("|", ", "),
                )
            )
        else:
            plugin_list = []
            is_xfs = lambda klass: any(
                k.__name__.startswith("XFS") for k in inspect.getmro(klass)
            )

            for p in self.pyload.plugin_manager.plugins[type].values():
                try:
                    klass = self.pyload.plugin_manager.load_class(type, p["name"])

                except AttributeError as exc:
                    self.log_debug(
                        exc,
                        exc_info=self.pyload.debug > 1,
                        stack_info=self.pyload.debug > 2,
                    )
                    continue

                if (
                    hasattr(klass, "PLUGIN_DOMAIN")
                    and klass.PLUGIN_DOMAIN
                    and is_xfs(klass)
                ):
                    plugin_list.append(klass.PLUGIN_DOMAIN)

            unmatch_list = "|".join(sorted(plugin_list)).replace(".", r"\.")
            pattern = self._regexmap[type][0].format(unmatch_list)

            self.log_info(self._("Auto-discover new {}s").format(type))

        return pattern

    def _load(self, type, plugin):
        dict = self.pyload.plugin_manager.plugins[type][plugin]
        pattern = self.get_pattern(type, plugin)

        if not pattern:
            return

        dict["pattern"] = pattern
        dict["re"] = re.compile(pattern)

        self.log_debug(f"Pattern for {type}: {pattern}")

    def _unload(self, type, plugin):
        dict = self.pyload.plugin_manager.plugins[type][plugin]
        dict["pattern"] = r"^unmatchable$"
        dict["re"] = re.compile(dict["pattern"])
