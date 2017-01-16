# -*- coding: utf-8 -*-

"""
Configuration layout for default base config.
"""
from __future__ import unicode_literals

#TODO: write tooltips and descriptions
#TODO: use apis config related classes

def make_config(config):
    # Check if gettext is installed
    _ = lambda x: x

    config.add_config_section("log", _("Log"), _("Description"), _("Long description"),
                            [
                                ("log_size", "int", _("Size in KiB"), 100),
                                ("log_folder", "folder", _("Folder"), "Logs"),
                                ("file_log", "bool", _("File Log"), True),
                                ("log_count", "int", _("Count"), 5),
                                ("log_rotate", "bool", _("Log Rotate"), True),
                                ("console_color", "bool", _("Colorize Console"), True),
                                ("color_theme", "light;full", _("Color Theme"), "light"),
                            ])

    config.add_config_section("permission", _("Permissions"), _("Description"), _("Long description"),
                            [
                                ("group", "str", _("Groupname"), "users"),
                                ("change_dl", "bool", _("Change Group and User of Downloads"), False),
                                ("change_file", "bool", _("Change file mode of downloads"), False),
                                ("user", "str", _("Username"), "user"),
                                ("file", "str", _("Filemode for Downloads"), "0644"),
                                ("change_group", "bool", _("Change group of running process"), False),
                                ("folder", "str", _("Folder Permission mode"), "0755"),
                                ("change_user", "bool", _("Change user of running process"), False),
                            ])

    config.add_config_section("general", _("General"), _("Description"), _("Long description"),
                            [
                                ("language", "en;de;fr;it;es;nl;sv;ru;pl;cs;sr;pt_BR", _("Language"), "en"),
                                ("download_folder", "folder", _("Download Folder"), "Downloads"),
                                ("folder_per_package", "bool", _("Create folder for each package"), True),
                                ("debug_mode", "bool", _("Debug Mode"), False),
                                ("min_free_space", "int", _("Min Free Space (MiB)"), 512),
                                ("renice", "int", _("CPU Priority"), 0),
                            ])

    config.add_config_section("ssl", _("SSL"), _("Description"), _("Long description"),
                            [
                                ("cert", "file", _("SSL Certificate"), "ssl.crt"),
                                ("activated", "bool", _("Activated"), False),
                                ("key", "file", _("SSL Key"), "ssl.key"),
                            ])

    config.add_config_section("webui", _("WebUI"), _("Description"), _("Long description"),
                            [
                                ("template", "str", _("Template"), "default"),
                                ("prefix", "str", _("Path Prefix"), ""),
                                ("external", "bool", _("Served external"), False),
                                ("server", "auto;threaded;fallback;fastcgi", _("Server"), "auto"),
                                ("force_server", "str", _("Favor specific server"), ""),
                                ("host", "ip", _("IP"), "localhost"),
                                ("https", "bool", _("Use HTTPS"), False),
                                ("port", "int", _("Port"), 8010),
                                ("wshost", "ip", _("IP"), "localhost"),
                                ("wsport", "int", _("Port"), 7447),
                            ])

    config.add_config_section("proxy", _("Proxy"), _("Description"), _("Long description"),
                            [
                                ("username", "str", _("Username"), ""),
                                ("proxy", "bool", _("Use Proxy"), False),
                                ("address", "str", _("Address"), "localhost"),
                                ("password", "password", _("Password"), ""),
                                ("type", "http;socks4;socks5", _("Protocol"), "http"),
                                ("port", "int", _("Port"), 7070),
                            ])

    config.add_config_section("reconnect", _("Reconnect"), _("Description"), _("Long description"),
                            [
                                ("activated", "bool", _("Use Reconnect"), False),
                                ("method", "str", _("Method"), "./reconnect.sh"),
                                ("wait", "str", _("Wait for reconnect"), False),
                                ("startTime", "time", _("Start"), "0:00"),
                                ("endTime", "time", _("End"), "0:00"),
                            ])

    config.add_config_section("download", _("Download"), _("Description"), _("Long description"),
                            [
                                ("max_downloads", "int", _("Max parallel downloads"), 3),
                                ("wait_downloads", "int", _("Start downloads while waiting"), 2),
                                ("limit_speed", "bool", _("Limit download speed"), False),
                                ("interface", "str", _("Download interface to bind (ip or Name)"), ""),
                                ("skip_existing", "bool", _("Skip already existing files"), False),
                                ("max_speed", "int", _("Max download speed in KiB/s"), -1),
                                ("ipv6", "bool", _("Allow IPv6"), False),
                                ("ssl", "bool", _("Force SSL downloads"), False),
                                ("chunks", "int", _("Max connections for one download"), 3),
                                ("restart_failed", "bool", _("Restart failed downloads on startup"), False),
                            ])

    config.add_config_section("downloadTime", _("Download Time"), _("Description"), _("Long description"),
                            [
                                ("start", "time", _("Start"), "0:00"),
                                ("end", "time", _("End"), "0:00"),
                            ])
