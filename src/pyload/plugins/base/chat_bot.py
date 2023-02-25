# -*- coding: utf-8 -*-

from threading import Thread

from pyload.core.api import FileDoesNotExists, PackageDoesNotExists
from pyload.core.utils import format

from .addon import BaseAddon


class ChatBot(Thread, BaseAddon):
    __name__ = "ChatBot"
    __type__ = "addon"
    __version__ = "0.02"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
    ]

    __description__ = """Base chat bot plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    SHORTCUT_COMMANDS = {
        "a": "add",
        "c": "collector",
        "ca": "captcha",
        "f": "freespace",
        "h": "help",
        "i": "info",
        "l": "getLog",
        "m": "more",
        "p": "packinfo",
        "q": "queue",
        "r": "restart",
        "rf": "restartfile",
        "rp": "restartpackage",
        "s": "status",
    }

    def __init__(self, *args, **kwargs):
        self.max_lines = 256
        self.more = []

        BaseAddon.__init__(self, *args, **kwargs)
        Thread.__init__(self)
        self.daemon = True

    def init(self):
        self.event_map = {
            "all_downloads_processed": "all_downloads_processed",
            "pyload_updated": "pyload_updated",
        }

    def all_downloads_processed(self):
        pass

    def pyload_updated(self, etag):
        pass

    def activate(self):
        Thread.start(self)

    def run(self):
        raise NotImplementedError

    def do_bot_command(self, cmd, args):
        cmd = self.SHORTCUT_COMMANDS.get(cmd.lower(), cmd.lower())
        handler = getattr(self, "_cmd_{}".format(cmd), self._cmd_error)
        return handler(args)

    def _cmd_error(self, args):
        return [self._("ERROR: invalid command, for a list of commands enter: help")]

    def _cmd_status(self, args):
        downloads = self.pyload.api.status_downloads()
        if not downloads:
            return [self._("INFO: There are no active downloads currently.")]

        lines = [self._("ID - Name - Status - Speed - ETA - Progress")]
        for data in downloads:
            if data.status == 5:
                temp_progress = data.format_wait
            else:
                temp_progress = "{}% ({})".format(data.percent, data.format_size)

            lines.append(
                "#{} - {} - {} - {} - {} - {}".format(
                    data.fid,
                    data.name,
                    data.statusmsg,
                    "{}".format(format.speed(data.speed)),
                    "{}".format(data.format_eta),
                    temp_progress,
                )
            )
        return lines

    def _cmd_queue(self, args):
        packages = self.pyload.api.get_queue_data()

        if not packages:
            return [self._("INFO: There are no packages in queue.")]

        lines = []
        for pack in packages:
            lines.append(
                'PACKAGE #{}: "{}" with {} links.'.format(
                    pack.pid, pack.name, len(pack.links)
                )
            )

        return lines

    def _cmd_collector(self, args):
        packages = self.pyload.api.get_collector_data()
        if not packages:
            return [self._("INFO: No packages in collector!")]

        lines = []
        for pack in packages:
            lines.append(
                'PACKAGE #{}: "{}" with {} links.'.format(
                    pack.pid, pack.name, len(pack.links)
                )
            )

        return lines

    def _cmd_info(self, args):
        try:
            file_id = int(args[0])

        except IndexError:
            return [
                self._("ERROR: Missing argument"),
                self._("Use info command like this: info <link id>"),
            ]

        except ValueError:
            return [self._("ERROR: invalid link id {}").format(args[0])]

        try:
            info = self.pyload.api.get_file_data(int(file_id))

        except FileDoesNotExists:
            return [self._("ERROR: Link doesn't exists.")]

        return [
            self._("LINK #{}: {} ({}) [{}][{}]").format(
                info.fid, info.name, info.format_size, info.statusmsg, info
            )
        ]

    def _cmd_packinfo(self, args):
        try:
            id_or_name = args[0]

        except IndexError:
            return [
                self._("ERROR: Missing argument"),
                self._("ERROR: Use packinfo like this: packinfo <name|id>"),
            ]

        lines = []

        pack = self._get_package_by_name_or_id(id_or_name)
        if not pack:
            return [self._("ERROR: Package doesn't exists.")]

        self.more = []

        lines.append(
            'PACKAGE #{}: "{}" with {} links:'.format(pack.pid, pack.name, len(pack.links))
        )
        for pyfile in pack.links:
            self.more.append(
                "LINK #{}: {} ({}) [{}]".format(
                    pyfile.fid,
                    pyfile.name,
                    pyfile.format_size,
                    pyfile.statusmsg,
                )
            )

        if len(self.more) < self.max_lines:
            lines.extend(self.more)
            self.more = []
        else:
            lines.extend(self.more[:self.max_lines])
            self.more = self.more[self.max_lines:]
            lines.append("{} more links to display.".format(len(self.more)))

        return lines

    def _cmd_more(self, args):
        if not self.more:
            return [self._("No more information to display.")]

        lines = self.more[:self.max_lines]
        self.more = self.more[self.max_lines:]
        lines.append("{} more links to display.".format(len(self.more)))

        return lines

    def _cmd_unpause(self, args):
        self.pyload.api.unpause_server()
        return [self._("INFO: Starting downloads.")]

    def _cmd_pause(self, args):
        self.pyload.api.pause_server()
        return [self._("INFO: No new downloads will be started.")]

    def _cmd_togglepause(self, args):
        if self.pyload.api.toggle_pause():
            return [self._("INFO: Starting downloads.")]
        else:
            return [self._("INFO: No new downloads will be started.")]

    def _cmd_add(self, args):
        if len(args) < 2:
            return [
                self._('ERROR: Add links like this: "add <name|id> link(s)". '),
                self._("This will add the link <link> to to the package name <name> / the package with id <id>!"),
            ]

        id_or_name = args[0].strip()
        links = [x.strip() for x in args[1:]]

        pack = self._get_package_by_name_or_id(id_or_name)
        if not pack:
            #: Create new package
            id = self.pyload.api.add_package(id_or_name, links, 1)
            return [
                self._("INFO: Created new Package {} [#{}] with {} links.").format(
                    id_or_name, id, len(links)
                )
            ]

        self.pyload.api.add_files(pack.pid, links)
        return [
            self._("INFO: Added {} links to Package {} [#{}]").format(
                len(links), pack.name, pack.pid
            )
        ]

    def _cmd_del(self, args):
        if len(args) < 2:
            return [
                self._("ERROR: Use del command like this: del -p|-l <id> [...]"),
                self._("(-p indicates that the ids are from packages,"),
                self._("-l indicates that the ids are from links"),
            ]

        if args[0] == "-p":
            ret = self.pyload.api.delete_packages(int(arg) for arg in args[1:])
            return [self._("INFO: Deleted {} packages!").format(len(args[1:]))]

        elif args[0] == "-l":
            ret = self.pyload.api.del_links(int(arg) for arg in args[1:])
            return [self._("INFO: Deleted {} links!").format(len(args[1:]))]

        else:
            return [
                self._("ERROR: Use del command like this: del <-p|-l> <id> [...]"),
                self._("-p indicates that the ids are from packages,"),
                self._("-l indicates that the ids are from links"),
            ]

    def _cmd_push(self, args):
        try:
            package_id = int(args[0])

        except IndexError:
            return [
                self._("ERROR: Missing argument"),
                self._("Push package to queue like this: push <package id>")
            ]

        except ValueError:
            return [self._("ERROR: invalid package id {}").format(args[0])]

        try:
            self.pyload.api.get_package_info(package_id)

        except PackageDoesNotExists:
            return [self._("ERROR: Package #{} does not exist.").format(package_id)]

        self.pyload.api.push_to_queue(package_id)
        return [self._("INFO: Pushed package #{} to queue.").format(package_id)]

    def _cmd_pull(self, args):
        try:
            package_id = int(args[0])

        except IndexError:
            return [
                self._("ERROR: Missing argument"),
                self._("Pull package from queue like this: pull <package id>"),
            ]

        except ValueError:
            return [self._("ERROR: invalid package id {}").format(args[0])]

        if not self.pyload.api.get_package_data(package_id):
            return [self._("ERROR: Package #{} does not exist.").format(package_id)]

        self.pyload.api.pull_from_queue(package_id)
        return [self._("INFO: Pulled package #{} from queue to collector.").format(package_id)]

    def _cmd_captcha(self, args):
        """
        Captcha answer.
        """
        if not args:
            return [self._("ERROR: Captcha ID missing.")]

        task = self.pyload.captcha_manager.get_task_by_id(args[0])
        if not task:
            return [self._("ERROR: Captcha Task with ID {} does not exists.").format(args[0])]

        task.set_result(" ".join(args[1:]))
        return [self._("INFO: Result {} saved.").format(" ".join(args[1:]))]

    def _cmd_freespace(self, args):
        b = format.size(int(self.pyload.api.free_space()))
        return [self._("INFO: Free space is {}.").format(b)]

    def _cmd_restart(self, args):
        self.pyload.api.restart()
        return [self._("INFO: Done.")]

    def _cmd_restartfailed(self, args):
        self.pyload.api.restart_failed()
        return [self._("INFO: Restarting all failed downloads.")]

    def _cmd_restartfile(self, args):
        try:
            file_id = int(args[0])

        except IndexError:
            return [
                self._("ERROR: Missing argument"),
                self._("Use restartfile command like this: pull <package id>"),
            ]

        except ValueError:
            return [self._("ERROR: Invalid file id")]

        if not self.pyload.api.get_file_data(file_id):
            return [self._("ERROR: File #{} does not exist.").format(file_id)]

        self.pyload.api.restart_file(file_id)
        return [self._("INFO: Restart file #{}.").format(file_id)]

    def _cmd_restartpackage(self, args):
        try:
            id_or_name = args[0]
        except IndexError:
            return [self._("ERROR: missing argument")]

        pack = self._get_package_by_name_or_id(id_or_name)
        if not pack:
            return [self._("ERROR: Package {} does not exist.").format(id_or_name)]
        self.pyload.api.restart_package(pack.pid)
        return [self._("INFO: Restart package {} (#{}).").format(pack.name, pack.pid)]

    def _cmd_deletefinished(self, args):
        return [self._("INFO: Deleted package ids: {}.").format(self.pyload.api.delete_finished())]

    def _cmd_getlog(self, args):
        """Returns most recent log entries."""
        self.more = []
        lines = []
        log = self.pyload.api.get_log()

        for line in log:
            if line:
                if line[-1] == '\n':
                    line = line[:-1]
                self.more.append("LOG: {}".format(line))

        if args and args[0] == 'last':
            if len(args) < 2:
                self.more = self.more[-self.max_lines:]
            else:
                self.more = self.more[-(int(args[1])):]

        if len(self.more) < self.max_lines:
            lines.extend(self.more)
            self.more = []
        else:
            lines.extend(self.more[:self.max_lines])
            self.more = self.more[self.max_lines:]
            lines.append("{} more logs to display.".format(len(self.more)))

        return lines

    def _cmd_help(self, args):
        lines = [
            "The following commands are available:",
            "add <package|packid> <links> [...] Adds link to package. (creates new package if it does not exist)",
            "captcha <id> <answer>              Solve a captcha task with id <id>",
            "collector                          Shows all packages in collector",
            "del -p|-l <id> [...]               Deletes all packages|links with the ids specified",
            "deletefinished                     Deletes all finished files and completly finished packages",
            "freespace                          Available free space at download directory in bytes",
            "getlog [last [nb]]                 Returns most recent log entries",
            "help                               Shows this help message",
            "info <id>                          Shows info of the link with id <id>",
            "more                               Shows more info when the result was truncated",
            "packinfo <package|packid>          Shows info of the package with id <id>",
            "pause                              Stops the download (but not abort active downloads)",
            "pull <id>                          Pull package from queue",
            "push <id>                          Push package to queue",
            "queue                              Shows all packages in the queue",
            "restart                            Restart pyload core",
            "restartfailed                      Restarts all failed files",
            "restartfile <id>                   Resets file status, so it will be downloaded again",
            "restartpackage <package|packid>    Restarts a package, resets every containing files",
            "status                             Show general download status",
            "togglepause                        Toggle pause state",
            "unpause                            Starts all downloads"
        ]
        lines.append("Shortcuts:")
        lines.append(", ".join(
            cmd_short + ": " + cmd_long
            for cmd_short, cmd_long in self.SHORTCUT_COMMANDS.items())
        )

        return lines

    def _get_package_by_name_or_id(self, id_or_name):
        """Return the first PackageData found or None."""
        if id_or_name.isdigit():
            try:
                package_id = int(id_or_name)
                pack = self.pyload.api.get_package_data(package_id)
            except PackageDoesNotExists:
                pack = self._get_package_by_name(id_or_name)
        else:
            pack = self._get_package_by_name(id_or_name)
        return pack

    def _get_package_by_name(self, name):
        """Return the first PackageData found or None."""
        pq = self.pyload.api.get_queue_data()
        for pack in pq:
            if pack.name == name:
                return pack

        pc = self.pyload.api.get_collector()
        for pack in pc:
            if pack.name == name:
                return pack
        return None
