# -*- coding: utf-8 -*-


from ..managers.event_manager import UpdateEvent
from ..utils.old import safepath


class PyPackage:
    """
    Represents a package object at runtime.
    """

    def __init__(self, manager, id, name, folder, site, password, queue, order):
        self.m = self.manager = manager
        self.m.package_cache[int(id)] = self

        self.id = int(id)
        self.name = name
        self._folder = folder
        self.site = site
        self.password = password
        self.queue = queue
        self.order = order
        self.set_finished = False

    @property
    def folder(self):
        return safepath(self._folder)

    def to_dict(self):
        """
        Returns a dictionary representation of the data.

        :return: dict: {id: { attr: value }}
        """
        return {
            self.id: {
                "id": self.id,
                "name": self.name,
                "folder": self.folder,
                "site": self.site,
                "password": self.password,
                "queue": self.queue,
                "order": self.order,
                "links": {},
            }
        }

    def get_children(self):
        """
        get information about contained links.
        """
        return self.m.get_package_data(self.id)["links"]

    def sync(self):
        """
        sync with db.
        """
        self.m.update_package(self)

    def release(self):
        """
        sync and delete from cache.
        """
        self.sync()
        self.m.release_package(self.id)

    def delete(self):
        self.m.delete_package(self.id)

    def notify_change(self):
        e = UpdateEvent("pack", self.id, "collector" if not self.queue else "queue")
        self.m.pyload.event_manager.add_event(e)
