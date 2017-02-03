# -*- coding: utf-8 -*-

"""
Configuration layout for default base config.
"""
from __future__ import unicode_literals

# TODO: write tooltips and descriptions
# TODO: use apis config related classes


def make_config(config):
    # Check if gettext is installed
    _ = lambda x: x

    config.add_config_section("general", _("General"), _("Description"), _("Long description"),
                              [
        ("language", "en|de|fr|it|es|nl|sv|ru|pl|cs|sr|pt", _("Language"), "en"),
        ("storage_folder", "folder", _("Storage folder"), None),
        ("min_storage_size", "int", _("Min storage space (in MiB)"), 512),
        ("folder_pack", "bool", _("Create folder for each package"), True),
        ("local_access", "bool", _("No authentication on local access"), True),
        ("niceness", "int", _("pyLoad process priority"), 0)
    ])

    config.add_config_section("log", _("Logging"), _("Description"), _("Long description"),
                              [
        ("activated", "bool", _("Activated"), True),
        ("logfile", "bool", _("Save log to file"), True),
        ("logfile_size", "int", _("Max file size (in KiB)"), 100),
        ("logfile_folder", "folder", _("File folder"), None),
        ("max_logfiles", "int", _("Max log files"), 5),
        ("rotate", "bool", _("Log rotate"), True),
        ("debug", "bool", _("Debug mode"), False),
        ("verbose", "bool", _("Verbose mode"), False),
        ("color_console", "bool", _("Color console"), True)
    ])

    config.add_config_section("permission", _("Permissions"), _("Description"), _("Long description"),
                              [
        ("user", "str", _("Username"), "user"),
        ("group", "str", _("Groupname"), "users"),
        ("foldermode", "str", _("Folder mode"), "0o755"),
        ("filemode", "str", _("File mode"), "0o644"),
        ("change_user", "bool", _("Change user of pyLoad process"), False),
        ("change_group", "bool", _("Change group of pyLoad process"), False),
        ("change_fileowner", "bool", _(
            "Change user and group of saved files"), False),
        ("change_filemode", "bool", _("Change file mode of saved files"), False)
    ])

    config.add_config_section("connection", _("Connections"), _("Description"), _("Long description"),
                              [
        ("max_transfers", "int", _("Max parallel transfers"), 5),
        ("max_speed", "int", _("Max transfer speed (in KiB/s)"), -1),
        ("max_chunks", "int", _("Max connections for single transfer"), -1),
        ("wait", "int", _("Active transfers while waiting"), 2),  # TODO: Recheck
        ("skip", "bool", _("Skip existing files"), False),
        ("interface", "str", _("Interface address to bind"), None),
        ("ipv6", "bool", _("Allow IPv6"), False)
    ])

    config.add_config_section("ssl", _("SSL"), _("Description"), _("Long description"),
                              [
        ("activated", "bool", _("Activated"), False),
        ("cert", "file", _("Cert file"), "ssl.crt"),
        ("key", "file", _("Key file"), "ssl.key")
    ])

    config.add_config_section("reconnect", _("Reconnection"), _("Description"), _("Long description"),
                              [
        ("activated", "bool", _("Activated"), False),
        ("script", "str", _("Script file"), None),
        ("wait", "str", _("Don't reconnect while waiting"), False)
    ])

    config.add_config_section("proxy", _("Proxy"), _("Description"), _("Long description"),
                              [
        ("activated", "bool", _("Activated"), False),
        ("type", "http|socks4|socks5", _("Protocol"), "http"),
        ("host", "str", _("IP address"), "localhost"),
        ("port", "int", _("Port"), 7070),
        ("username", "str", _("Username"), None),
        ("password", "str", _("Password"), None)
    ])

    config.add_config_section("webui", _("Web User Interface"), _("Description"), _("Long description"),
                              [
        ("activated", "bool", _("Activated"), True),
        ("server", "auto|threaded|fallback|fastcgi", _("Webserver"), "auto"),
        ("host", "str", _("IP address"), "localhost"),
        ("port", "int", _("Port"), 8010),
        ("force_server", "str", _("Forced webserver"), None),
        ("external", "bool", _("Served external"), False),
        ("prefix", "str", _("Path prefix"), None),
        ("debug", "bool", _("Debug mode"), False)
    ])

    config.add_config_section("remote", _("REST API Interface"), _("Description"), _("Long description"),
                              [
        ("activated", "bool", _("Activated"), False),
        ("host", "str", _("IP address"), "0.0.0.0"),
        ("port", "int", _("Port"), 7227)
    ])

    config.add_config_section("update", _("Updates"), _("Description"), _("Long description"),
                              [
        ("activated", "bool", _("Activated"), True),
        ("nodebug", "bool", _("Don't update in debug mode"), False),
        ("periodical", "bool", _("Check for updates on schedule"), True),
        ("interval", "int", _("Check interval (in days)"), 1)
    ])
