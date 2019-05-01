# -*- coding: utf-8 -*-
# AUTHOR: RaNaN
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

# import codecs
import os
import sys
import time

from threading import Lock, Thread

from easy_getch import getch

from pyload.core.datatypes.enums import Destination

# from pyload.core.remote.thriftbackend.thrift_client import (
# ConnectionClosed,
# NoConnection,
# NoSSL,
# ThriftClient,
# WrongLogin,
# )
from pyload.core.utils import decode, format_size, format_speed, lock

from .addpackage import AddPackage
from .managefiles import ManageFiles
from .printer import *

# if os.name == "nt":
# enc = "cp850"
# else:
# enc = "utf-8"
# sys.stdout = codecs.getwriter(enc)(sys.stdout, errors="replace")


def print_status(download):
    return "#{id:-6} {name:-40} Status: {statusmsg:-10} Size: {size}".format(
        id=download.fid,
        name=download.name,
        statusmsg=download.statusmsg,
        size=download.format_size,
    )


# TODO: use client.api instead client
class Cli:
    def __init__(self, client, command):
        self.client = client
        self.command = command
        self._ = client._

        if not self.command:
            # rename_process('pyLoadCLI')
            self.input = ""
            self.inputline = 0
            self.last_lowest_line = 0
            self.menuline = 0

            self.lock = Lock()

            # processor funcions, these will be changed dynamically depending on
            # control flow
            self.header_handler = self  #: the download status
            self.body_handler = self  #: the menu section
            self.input_handler = self

            os.system("clear")
            println(
                1,
                blue("py") + yellow("Load") + white(self._(" Command Line Interface")),
            )
            println(2, "")

            self.thread = RefreshThread(self)
            self.thread.start()

            self.start()
        else:
            self.process_command()

    def reset(self):
        """
        reset to initial main menu.
        """
        self.input = ""
        self.header_handler = self.body_handler = self.input_handler = self

    def start(self):
        """
        main loop.

        handle input
        """
        while True:
            inp = getch()
            if ord(inp) == 3:
                os.system("clear")
                sys.exit()  #: ctrl + c
            elif ord(inp) == 13:  #: enter
                with self.lock:
                    try:
                        self.input_handler.on_enter(self.input)
                    except Exception as exc:
                        println(2, red(exc))

            elif ord(inp) == 127:
                self.input = self.input[:-1]  #: backspace
                with self.lock:
                    self.input_handler.on_back_space()

            elif ord(inp) == 27:  #: ugly symbol
                pass
            else:
                self.input += inp
                with self.lock:
                    self.input_handler.on_char(inp)

            self.inputline = self.body_handler.render_body(self.menuline)
            self.render_footer(self.inputline)

    @lock
    def refresh(self):
        """
        refresh screen.
        """
        println(
            1, blue("py") + yellow("Load") + white(self._(" Command Line Interface"))
        )
        println(2, "")

        self.menuline = self.header_handler.render_header(3) + 1
        println(self.menuline - 1, "")
        self.inputline = self.body_handler.render_body(self.menuline)
        self.render_footer(self.inputline)

    def set_input(self, string=""):
        self.input = string

    def set_handler(self, klass):
        # create new handler with reference to cli
        self.body_handler = self.input_handler = klass(self)
        self.input = ""

    def render_header(self, line):
        """
        prints download status.
        """
        # print(updated information)
        #        print("\033[J" #clear screen)
        #        self.println(1, blue("py") + yellow("Load") + white(self._(" Command Line Interface")))
        #        self.println(2, "")
        #        self.println(3, white(self._("{} Downloads:").format(len(data))))

        data = self.client.status_downloads()
        speed = 0

        println(line, white(self._("{} Downloads:").format(len(data))))
        line += 1

        for download in data:
            if download.status == 12:  #: downloading
                percent = download.percent
                z = percent // 4
                speed += download.speed
                println(line, cyan(download.name))
                line += 1
                println(
                    line,
                    blue("[")
                    + yellow(z * "#" + (25 - z) * " ")
                    + blue("] ")
                    + green(str(percent) + "%")
                    + self._(" Speed: ")
                    + green(format_speed(download.speed))
                    + self._(" Size: ")
                    + green(download.format_size)
                    + self._(" Finished in: ")
                    + green(download.format_eta)
                    + self._(" ID: ")
                    + green(download.fid),
                )
                line += 1
            if download.status == 5:
                println(line, cyan(download.name))
                line += 1
                println(line, self._("waiting: ") + green(download.format_wait))
                line += 1

        println(line, "")
        line += 1
        status = self.client.status_server()
        if status.pause:
            paused = self._("Status:") + " " + red(self._("paused"))
        else:
            paused = self._("Status:") + " " + red(self._("running"))

        println(
            line,
            f'{paused} {self._("total Speed")}: {red(format_speed(speed))} {self._("Files in queue")}: {red(status.queue)} {self._("Total")}: {red(status.total)}',
        )

        return line + 1

    def render_body(self, line):
        """
        prints initial menu.
        """
        println(line, white(self._("Menu:")))
        println(line + 1, "")
        println(line + 2, mag("1.") + self._(" Add Links"))
        println(line + 3, mag("2.") + self._(" Manage Queue"))
        println(line + 4, mag("3.") + self._(" Manage Collector"))
        println(line + 5, mag("4.") + self._(" (Un)Pause Server"))
        println(line + 6, mag("5.") + self._(" Kill Server"))
        println(line + 7, mag("6.") + self._(" Quit"))

        return line + 8

    def render_footer(self, line):
        """
        prints out the input line with input.
        """
        println(line, "")
        line += 1

        println(line, white(" Input: ") + decode(self.input))

        # clear old output
        if line < self.last_lowest_line:
            for i in range(line + 1, self.last_lowest_line + 1):
                println(i, "")

        self.last_lowest_line = line

        # set cursor to position
        print(f"\033[{self.inputline};0H")

    def on_char(self, char):
        """
        default no special handling for single chars.
        """
        if char == "1":
            self.set_handler(AddPackage)
        elif char == "2":
            self.set_handler(ManageFiles)
        elif char == "3":
            self.set_handler(ManageFiles)
            self.body_handler.target = Destination.COLLECTOR
        elif char == "4":
            self.client.api.toggle_pause()
            self.set_input()
        elif char == "5":
            self.client.kill()
            self.client.close()
            sys.exit()
        elif char == "6":
            os.system("clear")
            sys.exit()

    def on_enter(self, inp):
        pass

    def on_back_space(self):
        pass

    def process_command(self):
        command = self.command[0]
        args = []
        if len(self.command) > 1:
            args = self.command[1:]

        if command == "status":
            files = self.client.status_downloads()

            if not files:
                print("No downloads running.")

            for download in files:
                if download.status == 12:  #: downloading
                    formatted_speed = format_speed(download.speed)
                    downloaded_size = format_size(download.size - download.bleft)
                    print(print_status(download))
                    print(
                        f"\t_downloading: {download.format_eta} @ {formatted_speed}\t {downloaded_size} ({download.percent}%%)"
                    )
                elif download.status == 5:
                    print(print_status(download))
                    print(f"\t_waiting: {download.format_wait}")
                else:
                    print(print_status(download))

        elif command == "queue":
            print_packages(self.client.get_queue_data())

        elif command == "collector":
            print_packages(self.client.get_collector_data())

        elif command == "add":
            if len(args) < 2:
                print(
                    self._(
                        "Please use this syntax: add <Package name> <link> <link2>..."
                    )
                )
                return

            self.client.add_package(args[0], args[1:], Destination.QUEUE)

        elif command == "add_coll":
            if len(args) < 2:
                print(
                    self._(
                        "Please use this syntax: add <Package name> <link> <link2>..."
                    )
                )
                return

            self.client.add_package(args[0], args[1:], Destination.COLLECTOR)

        elif command == "del_file":
            self.client.delete_files(int(x) for x in args)
            print("Files deleted.")

        elif command == "del_package":
            self.client.delete_packages(int(x) for x in args)
            print("Packages deleted.")

        elif command == "move":
            for pid in args:
                pack = self.client.get_package_info(int(pid))
                self.client.move_package((pack.dest + 1) % 2, pack.pid)

        elif command == "check":
            print(self._("Checking {} links:").format(len(args)))
            print()
            rid = self.client.check_online_status(args).rid
            self.print_online_check(self.client, rid)

        elif command == "check_container":
            path = args[0]
            if not os.path.exists(path):
                print(self._("File does not exists."))
                return

            with open(path, mode="rb") as file:
                content = file.read()

            rid = self.client.check_online_status_container(
                [], os.path.basename(file.name), content
            ).rid
            self.print_online_check(self.client, rid)

        elif command == "pause":
            self.client.pause()

        elif command == "unpause":
            self.client.unpause()

        elif command == "toggle":
            self.client.api.toggle_pause()

        elif command == "kill":
            self.client.kill()
        elif command == "restart_file":
            for x in args:
                self.client.restart_file(int(x))
            print("Files restarted.")
        elif command == "restart_package":
            for pid in args:
                self.client.restart_package(int(pid))
            print("Packages restarted.")

        else:
            print_commands()

    def print_online_check(self, client, rid):
        while True:
            time.sleep(1)
            result = client.poll_results(rid)
            for url, status in result.data.items():
                if status.status == 2:
                    check = "Online"
                elif status.status == 1:
                    check = "Offline"
                else:
                    check = "Unknown"

                print(
                    "{:-45} {:-12}\t {:-15}\t {}".format(
                        status.name, format_size(status.size), status.plugin, check
                    )
                )

            if result.rid == -1:
                break


class RefreshThread(Thread):
    def __init__(self, cli):
        super().__init__()
        self.daemon = True
        self.cli = cli
        self._ = cli._

    def run(self):
        while True:
            time.sleep(1)
            try:
                self.cli.refresh()
            except ConnectionClosed:
                os.system("clear")
                print(self._("pyLoad was terminated"))
                os._exit(0)
            except Exception as exc:
                println(2, red(exc))
                self.cli.reset()
