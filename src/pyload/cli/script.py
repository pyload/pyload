#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUTHOR: RaNaN, vuolter

import configparser
import os
import sys
from builtins import input
from getopt import GetoptError, getopt
from sys import exit

import pyload.core.utils.pylgettext as gettext
from pyload import DATADIR, PKGDIR
from pyload.core.remote.thriftbackend.thrift_client import (ConnectionClosed,
                                                            NoConnection, NoSSL,
                                                            ThriftClient, WrongLogin)

from . import Cli
from .printer import *


def print_help(config):
    print()
    print("pyLoad CLI Copyright (c) 2018 pyLoad team")
    print()
    print("Usage: pyLoadCLI [options] [command]")
    print()
    print("<Commands>")
    print("See pyLoadCLI -c for a complete listing.")
    print()
    print("<Options>")
    print("  -i, --interactive", " Start in interactive mode")
    print()
    print("  -u, --username=", " " * 2, "Specify Username")
    print("  --pw=<password>", " " * 2, "Password")
    addr = config["addr"]
    print(
        "  -a, --address=",
        " " * 3,
        f"Specify address (current={addr})",
    )
    port = config["port"]
    print(f"  -p, --port", " " * 7, "Specify port (current={port})")
    print()
    lang = config["language"]
    print(
        "  -l, --language",
        " " * 3,
        f"Set user interface language (current={lang})",
    )
    print("  -h, --help", " " * 7, "Display this help screen")
    print("  -c, --commands", " " * 3, "List all available commands")
    print()


def print_packages(data):
    for pack in data:
        print(f"Package {pack.name} (#{pack.pid}):")
        for download in pack.links:
            print("\t" + print_file(download))
        print()


def print_file(download):
    return "#{id:-6d} {name:-30} {statusmsg:-10} {plugin:-8}".format(
        id=download.fid,
        name=download.name,
        statusmsg=download.statusmsg,
        plugin=download.plugin,
    )


def print_commands():
    commands = [
        ("status", self._("Prints server status")),
        ("queue", self._("Prints downloads in queue")),
        ("collector", self._("Prints downloads in collector")),
        ("add <name> <link1> <link2>...", self._("Adds package to queue")),
        ("add_coll <name> <link1> <link2>...", self._("Adds package to collector")),
        ("del_file <fid> <fid2>...", self._("Delete Files from Queue/Collector")),
        ("del_package <pid> <pid2>...", self._("Delete Packages from Queue/Collector")),
        (
            "move <pid> <pid2>...",
            self._("Move Packages from Queue to Collector or vice versa"),
        ),
        ("restart_file <fid> <fid2>...", self._("Restart files")),
        ("restart_package <pid> <pid2>...", self._("Restart packages")),
        (
            "check <container|url>...",
            self._("Check online status, works with local container"),
        ),
        ("check_container path", self._("Checks online status of a container file")),
        ("pause", self._("Pause the server")),
        ("unpause", self._("continue downloads")),
        ("toggle", self._("Toggle pause/unpause")),
        ("kill", self._("kill server")),
    ]

    print(self._("List of commands:"))
    print()
    for c in commands:
        print(f"%-35s {c}")


def writeConfig(opts):
    try:
        with open(os.path.join(DATADIR, "pyload-cli.conf"), mode="w") as cfgfile:
            cfgfile.write("[cli]")
            for opt in opts:
                cfgfile.write(f"{opt}={opts[opt]}\n")
    except Exception:
        print(self._("Couldn't write user config file"))


def run():
    config = {"addr": "127.0.0.1", "port": "7227", "language": "en"}
    try:
        config["language"] = os.environ["LANG"][0:2]
    except Exception:
        pass

    if (
        not os.path.exists(os.path.join(PKGDIR, "locale", config["language"]))
    ) or config["language"] == "":
        config["language"] = "en"

    configFile = configparser.ConfigParser()
    configFile.read(os.path.join(DATADIR, "pyload-cli.conf"))

    if configFile.has_section("cli"):
        for opt in configFile.items("cli"):
            config[opt[0]] = opt[1]

    gettext.setpaths([os.path.join(os.sep, "usr", "share", "pyload", "locale"), None])
    translation = gettext.translation(
        "cli",
        os.path.join(PKGDIR, "locale"),
        languages=[config["language"], "en"],
        fallback=True,
    )
    translation.install(str=True)

    interactive = False
    command = None
    username = ""
    password = ""

    shortOptions = "iu:p:a:hcl:"
    longOptions = [
        "interactive",
        "username=",
        "pw=",
        "address=",
        "port=",
        "help",
        "commands",
        "language=",
    ]

    try:
        opts, extraparams = getopt(sys.argv[1:], shortOptions, longOptions)
        for option, params in opts:
            if option in ("-i", "--interactive"):
                interactive = True
            elif option in ("-u", "--username"):
                username = params
            elif option in ("-a", "--address"):
                config["addr"] = params
            elif option in ("-p", "--port"):
                config["port"] = params
            elif option in ("-l", "--language"):
                config["language"] = params
                gettext.setpaths(
                    [os.path.join(os.sep, "usr", "share", "pyload", "locale"), None]
                )
                translation = gettext.translation(
                    "cli",
                    os.path.join(PKGDIR, "locale"),
                    languages=[config["language"], "en"],
                    fallback=True,
                )
                translation.install(str=True)
            elif option in ("-h", "--help"):
                print_help(config)
                exit()
            elif option in ("--pw"):
                password = params
            elif option in ("-c", "--comands"):
                print_commands()
                exit()

    except GetoptError:
        print('Unknown Argument(s) "{}"'.format(" ".join(sys.argv[1:])))
        print_help(config)
        exit()

    if len(extraparams) >= 1:
        command = extraparams

    client = False

    if interactive:
        try:
            client = ThriftClient(
                config["addr"], int(config["port"]), username, password
            )
        except WrongLogin:
            pass
        except NoSSL:
            print(self._("You need py-openssl to connect to this pyLoad Core."))
            exit()
        except NoConnection:
            config["addr"] = False
            config["port"] = False

        if not client:
            if not config["addr"]:
                config["addr"] = input(self._("Address: "))
            if not config["port"]:
                config["port"] = input(self._("Port: "))
            if not username:
                username = input(self._("Username: "))
            if not password:
                from getpass import getpass

                password = getpass(self._("Password: "))

            try:
                client = ThriftClient(
                    config["addr"], int(config["port"]), username, password
                )
            except WrongLogin:
                print(self._("Login data is wrong."))
            except NoConnection:
                print(
                    self._("Could not establish connection to {addr}:{port}").format(
                        addr=config["addr"], port=config["port"]
                    )
                )

    else:
        try:
            client = ThriftClient(
                config["addr"], int(config["port"]), username, password
            )
        except WrongLogin:
            print(self._("Login data is wrong."))
        except NoConnection:
            print(
                self._("Could not establish connection to {addr}:{port}").format(
                    addr=config["addr"], port=config["port"]
                )
            )
        except NoSSL:
            print(self._("You need py-openssl to connect to this pyLoad core."))

    if interactive and command:
        print(self._("Interactive mode ignored since you passed some commands."))

    if client:
        writeConfig(config)
        Cli(client, command)


def main():
    """
    Entry point for console_scripts.
    """
    # args = parse_args(sys.argv[1:])
    run()


if __name__ == "__main__":
    main()
