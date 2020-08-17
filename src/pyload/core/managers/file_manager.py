# -*- coding: utf-8 -*-

from threading import RLock

from ..datatypes.enums import Destination
from ..utils.old import lock
from .event_manager import InsertEvent, ReloadAllEvent, RemoveEvent, UpdateEvent


class FileManager:
    """
    Handles all request made to obtain information, modify status or other request for
    links or packages.
    """

    def __init__(self, core):
        """
        Constructor.
        """
        self.pyload = core
        self._ = core._

        # translations
        self.status_msg = [
            self._("finished"),
            self._("offline"),
            self._("online"),
            self._("queued"),
            self._("skipped"),
            self._("waiting"),
            self._("temp. offline"),
            self._("starting"),
            self._("failed"),
            self._("aborted"),
            self._("decrypting"),
            self._("custom"),
            self._("downloading"),
            self._("processing"),
            self._("unknown"),
        ]

        # TODO: purge the cache
        self.cache = {}  #: holds instances for files
        self.package_cache = {}  #: same for packages

        self.job_cache = {}

        self.lock = RLock()  # TODO: should be a Lock w/o R
        # self.lock._Verbose__verbose = True

        self.filecount = -1  #: if an invalid value is set get current value from db
        self.queuecount = -1  #: number of package to be loaded
        self.unchanged = False  #: determines if any changes was made since last call

    def change(func):
        def new(*args):
            args[0].unchanged = False
            args[0].filecount = -1
            args[0].queuecount = -1
            args[0].job_cache = {}
            return func(*args)

        return new

    # ----------------------------------------------------------------------
    def save(self):
        """
        saves all data to backend.
        """
        self.pyload.db.commit()

    # ----------------------------------------------------------------------
    def sync_save(self):
        """
        saves all data to backend and waits until all data are written.
        """
        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            pyfile.sync()

        pypacks = self.package_cache.values()
        for pypack in pypacks:
            pypack.sync()

        self.pyload.db.sync_save()

    @lock
    def get_complete_data(self, queue=Destination.QUEUE):
        """
        gets a complete data representation.
        """
        queue = queue.value
        data = self.pyload.db.get_all_links(queue)
        packs = self.pyload.db.get_all_packages(queue)

        data.update((x.id, x.to_db_dict()[x.id]) for x in self.cache.values())

        for x in self.package_cache.values():
            if x.queue != queue or x.id not in packs:
                continue
            packs[x.id].update(x.to_dict()[x.id])

        for key, value in data.items():
            if value["package"] in packs:
                packs[value["package"]]["links"][key] = value

        return packs

    @lock
    def get_info_data(self, queue=Destination.QUEUE):
        """
        gets a data representation without links.
        """
        queue = queue.value
        packs = self.pyload.db.get_all_packages(queue)
        for x in self.package_cache.values():
            if x.queue != queue or x.id not in packs:
                continue
            packs[x.id].update(x.to_dict()[x.id])

        return packs

    @lock
    @change
    def add_links(self, urls, package):
        """
        adds links.
        """
        self.pyload.addon_manager.dispatch_event("links_added", urls, package)

        data = self.pyload.plugin_manager.parse_urls(urls)

        self.pyload.db.add_links(data, package)
        self.pyload.thread_manager.create_info_thread(data, package)

        # TODO: change from reload_all event to package update event
        self.pyload.event_manager.add_event(ReloadAllEvent("collector"))

    # ----------------------------------------------------------------------
    @lock
    @change
    def add_package(self, name, folder, queue=Destination.QUEUE):
        """
        adds a package, default to link collector.
        """
        last_id = self.pyload.db.add_package(name, folder, queue.value)
        p = self.pyload.db.get_package(last_id)
        e = InsertEvent(
            "pack",
            last_id,
            p.order,
            "collector" if queue is Destination.COLLECTOR else "queue",
        )
        self.pyload.event_manager.add_event(e)
        return last_id

    # ----------------------------------------------------------------------
    @lock
    @change
    def delete_package(self, id):
        """
        delete package and all contained links.
        """
        p = self.get_package(id)
        if not p:
            if id in self.package_cache:
                del self.package_cache[id]
            return

        oldorder = p.order
        queue = p.queue

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == id:
                pyfile.abort_download()
                pyfile.release()

        self.pyload.db.delete_package(p)
        self.pyload.event_manager.add_event(e)
        self.pyload.addon_manager.dispatch_event("package_deleted", id)

        if id in self.package_cache:
            del self.package_cache[id]

        packs = self.package_cache.values()
        for pack in packs:
            if pack.queue == queue and pack.order > oldorder:
                pack.order -= 1
                pack.notify_change()

    # ----------------------------------------------------------------------
    @lock
    @change
    def delete_link(self, id):
        """
        deletes links.
        """
        f = self.get_file(id)
        if not f:
            return None

        pid = f.packageid
        e = RemoveEvent("file", id, "collector" if not f.package().queue else "queue")

        oldorder = f.order

        if id in self.pyload.thread_manager.processing_ids():
            self.cache[id].abort_download()

        if id in self.cache:
            del self.cache[id]

        self.pyload.db.delete_link(f)

        self.pyload.event_manager.add_event(e)

        p = self.get_package(pid)
        if not len(p.get_children()):
            p.delete()

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == pid and pyfile.order > oldorder:
                pyfile.order -= 1
                pyfile.notify_change()

    # ----------------------------------------------------------------------
    def release_link(self, id):
        """
        removes pyfile from cache.
        """
        if id in self.cache:
            del self.cache[id]

    # ----------------------------------------------------------------------
    def release_package(self, id):
        """
        removes package from cache.
        """
        if id in self.package_cache:
            del self.package_cache[id]

    # ----------------------------------------------------------------------
    def update_link(self, pyfile):
        """
        updates link.
        """
        self.pyload.db.update_link(pyfile)

        e = UpdateEvent(
            "file", pyfile.id, "collector" if not pyfile.package().queue else "queue"
        )
        self.pyload.event_manager.add_event(e)

    # ----------------------------------------------------------------------
    def update_package(self, pypack):
        """
        updates a package.
        """
        self.pyload.db.update_package(pypack)

        e = UpdateEvent("pack", pypack.id, "collector" if not pypack.queue else "queue")
        self.pyload.event_manager.add_event(e)

    # ----------------------------------------------------------------------
    def get_package(self, id):
        """
        return package instance.
        """
        if id in self.package_cache:
            return self.package_cache[id]
        else:
            return self.pyload.db.get_package(id)

    # ----------------------------------------------------------------------
    def get_package_data(self, id):
        """
        returns dict with package information.
        """
        pack = self.get_package(id)

        if not pack:
            return None

        pack = pack.to_dict()[id]

        data = self.pyload.db.get_package_data(id)

        tmplist = []

        cache = self.cache.values()
        for x in cache:
            if int(x.to_db_dict()[x.id]["package"]) == int(id):
                tmplist.append((x.id, x.to_db_dict()[x.id]))
        data.update(tmplist)

        pack["links"] = data

        return pack

    # ----------------------------------------------------------------------
    def get_file_data(self, id):
        """
        returns dict with file information.
        """
        if id in self.cache:
            return self.cache[id].to_db_dict()

        return self.pyload.db.get_link_data(id)

    # ----------------------------------------------------------------------
    def get_file(self, id):
        """
        returns pyfile instance.
        """
        if id in self.cache:
            return self.cache[id]
        else:
            return self.pyload.db.get_file(id)

    # ----------------------------------------------------------------------
    @lock
    def get_job(self, occ):
        """
        get suitable job.
        """
        # TODO: clean mess
        # TODO: improve selection of valid jobs

        if occ in self.job_cache:
            if self.job_cache[occ]:
                id = self.job_cache[occ].pop()
                if id == "empty":
                    pyfile = None
                    self.job_cache[occ].append("empty")
                else:
                    pyfile = self.get_file(id)
            else:
                jobs = self.pyload.db.get_job(occ)
                jobs.reverse()
                if not jobs:
                    self.job_cache[occ].append("empty")
                    pyfile = None
                else:
                    self.job_cache[occ].extend(jobs)
                    pyfile = self.get_file(self.job_cache[occ].pop())

        else:
            self.job_cache = {}  #: better not caching to much
            jobs = self.pyload.db.get_job(occ)
            jobs.reverse()
            self.job_cache[occ] = jobs

            if not jobs:
                self.job_cache[occ].append("empty")
                pyfile = None
            else:
                pyfile = self.get_file(self.job_cache[occ].pop())

            # TODO: maybe the new job has to be approved...

        # pyfile = self.get_file(self.job_cache[occ].pop())
        return pyfile

    @lock
    def get_decrypt_job(self):
        """
        return job for decrypting.
        """
        if "decrypt" in self.job_cache:
            return None

        plugins = list(self.pyload.plugin_manager.crypter_plugins.keys()) + list(
            self.pyload.plugin_manager.container_plugins.keys()
        )
        plugins = str(tuple(plugins))

        jobs = self.pyload.db.get_plugin_job(plugins)
        if jobs:
            return self.get_file(jobs[0])
        else:
            self.job_cache["decrypt"] = "empty"
            return None

    def get_file_count(self):
        """
        returns number of files.
        """
        if self.filecount == -1:
            self.filecount = self.pyload.db.filecount(1)

        return self.filecount

    def get_queue_count(self, force=False):
        """
        number of files that have to be processed.
        """
        if self.queuecount == -1 or force:
            self.queuecount = self.pyload.db.queuecount(1)

        return self.queuecount

    def check_all_links_finished(self):
        """
        checks if all files are finished and dispatch event.
        """
        if not self.get_queue_count(True):
            self.pyload.addon_manager.dispatch_event("all_downloads_finished")
            self.pyload.log.debug("All downloads finished")
            return True

        return False

    def check_all_links_processed(self, fid):
        """
        checks if all files was processed and pyload would idle now, needs fid which
        will be ignored when counting.
        """
        # reset count so statistic will update (this is called when dl was processed)
        self.reset_count()

        if not self.pyload.db.processcount(1, fid):
            self.pyload.addon_manager.dispatch_event("all_downloads_processed")
            self.pyload.log.debug("All downloads processed")
            return True

        return False

    def reset_count(self):
        self.queuecount = -1

    @lock
    @change
    def restart_package(self, id):
        """
        restart package.
        """
        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == id:
                self.restart_file(pyfile.id)

        self.pyload.db.restart_package(id)

        if id in self.package_cache:
            self.package_cache[id].set_finished = False

        e = UpdateEvent(
            "pack", id, "collector" if not self.get_package(id).queue else "queue"
        )
        self.pyload.event_manager.add_event(e)

    @lock
    @change
    def restart_file(self, id):
        """
        restart file.
        """
        if id in self.cache:
            self.cache[id].status = 3
            self.cache[id].name = self.cache[id].url
            self.cache[id].error = ""
            self.cache[id].abort_download()

        self.pyload.db.restart_file(id)

        e = UpdateEvent(
            "file",
            id,
            "collector" if not self.get_file(id).package().queue else "queue",
        )
        self.pyload.event_manager.add_event(e)

    @lock
    @change
    def set_package_location(self, id, queue):
        """
        push package to queue.
        """
        queue = queue.value
        p = self.pyload.db.get_package(id)
        oldorder = p.order

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")
        self.pyload.event_manager.add_event(e)

        self.pyload.db.clear_package_order(p)

        p = self.pyload.db.get_package(id)

        p.queue = queue
        self.pyload.db.update_package(p)

        self.pyload.db.reorder_package(p, -1, True)

        packs = self.package_cache.values()
        for pack in packs:
            if pack.queue != queue and pack.order > oldorder:
                pack.order -= 1
                pack.notify_change()

        self.pyload.db.commit()
        self.release_package(id)
        p = self.get_package(id)

        e = InsertEvent("pack", id, p.order, "collector" if not p.queue else "queue")
        self.pyload.event_manager.add_event(e)

    @lock
    @change
    def reorder_package(self, id, position):
        p = self.get_package(id)

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")
        self.pyload.event_manager.add_event(e)
        self.pyload.db.reorder_package(p, position)

        packs = self.package_cache.values()
        for pack in packs:
            if pack.queue != p.queue or pack.order < 0 or pack == p:
                continue
            if p.order > position:
                if pack.order >= position and pack.order < p.order:
                    pack.order += 1
                    pack.notify_change()
            elif p.order < position:
                if pack.order <= position and pack.order > p.order:
                    pack.order -= 1
                    pack.notify_change()

        p.order = position
        self.pyload.db.commit()

        e = InsertEvent("pack", id, position, "collector" if not p.queue else "queue")
        self.pyload.event_manager.add_event(e)

    @lock
    @change
    def reorder_file(self, id, position):
        f = self.get_file_data(id)
        f = f[id]

        e = RemoveEvent(
            "file",
            id,
            "collector" if not self.get_package(f["package"]).queue else "queue",
        )
        self.pyload.event_manager.add_event(e)

        self.pyload.db.reorder_link(f, position)

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid != f["package"] or pyfile.order < 0:
                continue
            if f["order"] > position:
                if pyfile.order >= position and pyfile.order < f["order"]:
                    pyfile.order += 1
                    pyfile.notify_change()
            elif f["order"] < position:
                if pyfile.order <= position and pyfile.order > f["order"]:
                    pyfile.order -= 1
                    pyfile.notify_change()

        if id in self.cache:
            self.cache[id].order = position

        self.pyload.db.commit()

        e = InsertEvent(
            "file",
            id,
            position,
            "collector" if not self.get_package(f["package"]).queue else "queue",
        )
        self.pyload.event_manager.add_event(e)

    @change
    def update_file_info(self, data, pid):
        """
        updates file info (name, size, status, url)
        """
        self.pyload.db.update_link_info(data)
        e = UpdateEvent(
            "pack", pid, "collector" if not self.get_package(pid).queue else "queue"
        )
        self.pyload.event_manager.add_event(e)

    def check_package_finished(self, pyfile):
        """
        checks if package is finished and calls addon_manager.
        """
        ids = self.pyload.db.get_unfinished(pyfile.packageid)
        if not ids or (pyfile.id in ids and len(ids) == 1):
            if not pyfile.package().set_finished:
                self.pyload.log.info(
                    self._("Package finished: {}").format(pyfile.package().name)
                )
                self.pyload.addon_manager.package_finished(pyfile.package())
                pyfile.package().set_finished = True

    def re_check_package(self, pid):
        """
        recheck links in package.
        """
        data = self.pyload.db.get_package_data(pid)

        urls = []

        for pyfile in data.values():
            if pyfile["status"] not in (0, 12, 13):
                urls.append((pyfile["url"], pyfile["plugin"]))

        self.pyload.thread_manager.create_info_thread(urls, pid)

    @lock
    @change
    def delete_finished_links(self):
        """
        deletes finished links and packages, return deleted packages.
        """
        old_packs = self.get_info_data(0)
        old_packs.update(self.get_info_data(1))

        self.pyload.db.delete_finished()

        new_packs = self.pyload.db.get_all_packages(0)
        new_packs.update(self.pyload.db.get_all_packages(1))
        # get new packages only from db

        deleted = []
        for id in old_packs.keys():
            if id not in new_packs:
                deleted.append(id)
                self.delete_package(int(id))

        return deleted

    @lock
    @change
    def restart_failed(self):
        """
        restart all failed links.
        """
        self.pyload.db.restart_failed()
