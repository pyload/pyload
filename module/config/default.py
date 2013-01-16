# -*- coding: utf-8 -*-

"""
Configuration layout for default base config
"""

#TODO: write tooltips and descriptions

def make_config(config):
    # Check if gettext is installed
    _ = lambda x: x

    config.addConfigSection("remote", _("Remote"), _("Description"), _("Long description"),
        [
            ("nolocalauth", "bool", _("No authentication on local connections"), _("Tooltip"), True),
            ("activated", "bool", _("Activated"), _("Tooltip"), True),
            ("port", "int", _("Port"), _("Tooltip"), 7227),
            ("listenaddr", "ip", _("Adress"), _("Tooltip"), "0.0.0.0"),
        ])

    config.addConfigSection("log", _("Log"), _("Description"), _("Long description"),
        [
            ("log_size", "int", _("Size in kb"), _("Tooltip"), 100),
            ("log_folder", "folder", _("Folder"), _("Tooltip"), "Logs"),
            ("file_log", "bool", _("File Log"), _("Tooltip"), True),
            ("log_count", "int", _("Count"), _("Tooltip"), 5),
            ("log_rotate", "bool", _("Log Rotate"), _("Tooltip"), True),
        ])

    config.addConfigSection("permission", _("Permissions"), _("Description"), _("Long description"),
        [
            ("group", "str", _("Groupname"), _("Tooltip"), "users"),
            ("change_dl", "bool", _("Change Group and User of Downloads"), _("Tooltip"), False),
            ("change_file", "bool", _("Change file mode of downloads"), _("Tooltip"), False),
            ("user", "str", _("Username"), _("Tooltip"), "user"),
            ("file", "str", _("Filemode for Downloads"), _("Tooltip"), "0644"),
            ("change_group", "bool", _("Change group of running process"), _("Tooltip"), False),
            ("folder", "str", _("Folder Permission mode"), _("Tooltip"), "0755"),
            ("change_user", "bool", _("Change user of running process"), _("Tooltip"), False),
        ])

    config.addConfigSection("general", _("General"), _("Description"), _("Long description"),
        [
            ("language", "en;de;fr;it;es;nl;sv;ru;pl;cs;sr;pt_BR", _("Language"), _("Tooltip"), "en"),
            ("download_folder", "folder", _("Download Folder"), _("Tooltip"), "Downloads"),
            ("checksum", "bool", _("Use Checksum"), _("Tooltip"), False),
            ("folder_per_package", "bool", _("Create folder for each package"), _("Tooltip"), True),
            ("debug_mode", "bool", _("Debug Mode"), _("Tooltip"), False),
            ("min_free_space", "int", _("Min Free Space (MB)"), _("Tooltip"), 200),
            ("renice", "int", _("CPU Priority"), _("Tooltip"), 0),
        ])

    config.addConfigSection("ssl", _("SSL"), _("Description"), _("Long description"),
        [
            ("cert", "file", _("SSL Certificate"), _("Tooltip"), "ssl.crt"),
            ("activated", "bool", _("Activated"), _("Tooltip"), False),
            ("key", "file", _("SSL Key"), _("Tooltip"), "ssl.key"),
        ])

    config.addConfigSection("webinterface", _("Webinterface"), _("Description"), _("Long description"),
        [
            ("template", "str", _("Template"), _("Tooltip"), "default"),
            ("activated", "bool", _("Activated"), _("Tooltip"), True),
            ("prefix", "str", _("Path Prefix"), _("Tooltip"), ""),
            ("server", "auto;threaded;fallback;fastcgi", _("Server"), _("Tooltip"), "auto"),
            ("force_server", "str", _("Favor specific server"), _("Tooltip"), ""),
            ("host", "ip", _("IP"), _("Tooltip"), "0.0.0.0"),
            ("https", "bool", _("Use HTTPS"), _("Tooltip"), False),
            ("port", "int", _("Port"), _("Tooltip"), 8001),
        ])

    config.addConfigSection("proxy", _("Proxy"), _("Description"), _("Long description"),
        [
            ("username", "str", _("Username"), _("Tooltip"), ""),
            ("proxy", "bool", _("Use Proxy"), _("Tooltip"), False),
            ("address", "str", _("Address"), _("Tooltip"), "localhost"),
            ("password", "password", _("Password"), _("Tooltip"), ""),
            ("type", "http;socks4;socks5", _("Protocol"), _("Tooltip"), "http"),
            ("port", "int", _("Port"), _("Tooltip"), 7070),
        ])

    config.addConfigSection("reconnect", _("Reconnect"), _("Description"), _("Long description"),
        [
            ("endTime", "time", _("End"), _("Tooltip"), "0:00"),
            ("activated", "bool", _("Use Reconnect"), _("Tooltip"), False),
            ("method", "str", _("Method"), _("Tooltip"), "./reconnect.sh"),
            ("startTime", "time", _("Start"), _("Tooltip"), "0:00"),
        ])

    config.addConfigSection("download", _("Download"), _("Description"), _("Long description"),
        [
            ("max_downloads", "int", _("Max Parallel Downloads"), _("Tooltip"), 3),
            ("limit_speed", "bool", _("Limit Download Speed"), _("Tooltip"), False),
            ("interface", "str", _("Download interface to bind (ip or Name)"), _("Tooltip"), ""),
            ("skip_existing", "bool", _("Skip already existing files"), _("Tooltip"), False),
            ("max_speed", "int", _("Max Download Speed in kb/s"), _("Tooltip"), -1),
            ("ipv6", "bool", _("Allow IPv6"), _("Tooltip"), False),
            ("chunks", "int", _("Max connections for one download"), _("Tooltip"), 3),
            ("restart_failed", "bool", _("Restart failed downloads on startup"), _("Tooltip"), False),
        ])

    config.addConfigSection("downloadTime", _("Download Time"), _("Description"), _("Long description"),
        [
            ("start", "time", _("Start"), _("Tooltip"), "0:00"),
            ("end", "time", _("End"), _("Tooltip"), "0:00"),
        ])
