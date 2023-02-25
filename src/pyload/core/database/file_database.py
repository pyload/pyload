# -*- coding: utf-8 -*-

from ..datatypes.pyfile import PyFile
from ..datatypes.pypackage import PyPackage
from ..utils import format
from ..utils.struct.style import style
from ..utils.web import parse


class FileDatabaseMethods:
    @style.queue
    def filecount(self, queue):
        """
        returns number of files in queue.
        """
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=?",
            (queue,),
        )
        return self.c.fetchone()[0]

    @style.queue
    def queuecount(self, queue):
        """
        number of files in queue not finished yet.
        """
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? AND l.status NOT IN (0,4)",
            (queue,),
        )
        return self.c.fetchone()[0]

    @style.queue
    def processcount(self, queue, fid):
        """
        number of files which have to be processed.
        """
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? AND l.status IN (2,3,5,7,12) AND l.id != ?",
            (queue, str(fid)),
        )
        return self.c.fetchone()[0]

    @style.inner
    def _next_package_order(self, queue=0):
        self.c.execute("SELECT MAX(packageorder) FROM packages WHERE queue=?", (queue,))
        max_order = self.c.fetchone()[0]
        if max_order is not None:
            return max_order + 1
        else:
            return 0

    @style.inner
    def _next_file_order(self, package):
        self.c.execute("SELECT MAX(linkorder) FROM links WHERE package=?", (package,))
        max_order = self.c.fetchone()[0]
        if max_order is not None:
            return max_order + 1
        else:
            return 0

    @style.queue
    def add_link(self, url, name, plugin, package):
        order = self._next_file_order(package)
        self.c.execute(
            "INSERT INTO links(url, name, plugin, package, linkorder) VALUES(?,?,?,?,?)",
            (url, name, plugin, package, order),
        )
        return self.c.lastrowid

    @style.queue
    def add_links(self, links, package):
        """
        links is a list of tuples (url,plugin)
        """
        order = self._next_file_order(package)
        orders = [order + x for x in range(len(links))]
        links = [(x[0], parse.name(x[0]), x[1], package, o) for x, o in zip(links, orders)]
        self.c.executemany(
            "INSERT INTO links(url, name, plugin, package, linkorder) VALUES(?,?,?,?,?)",
            links,
        )

    @style.queue
    def add_package(self, name, folder, queue):
        order = self._next_package_order(queue)
        self.c.execute(
            "INSERT INTO packages(name, folder, queue, packageorder) VALUES(?,?,?,?)",
            (name, folder, queue, order),
        )
        return self.c.lastrowid

    @style.queue
    def delete_package(self, p):
        self.c.execute("DELETE FROM links WHERE package=?", (str(p.id),))
        self.c.execute("DELETE FROM packages WHERE id=?", (str(p.id),))
        self.c.execute(
            "UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > ? AND queue=?",
            (p.order, p.queue),
        )

    @style.queue
    def delete_link(self, f):
        self.c.execute("DELETE FROM links WHERE id=?", (str(f.id),))
        self.c.execute(
            "UPDATE links SET linkorder=linkorder-1 WHERE linkorder > ? AND package=?",
            (f.order, str(f.packageid)),
        )

    @style.queue
    def get_all_links(self, q):
        """
        return information about all links in queue q.

        q0 queue
        q1 collector

        format:

        {
            id: {'name': name, ... 'package': id }, ...
        }
        """
        self.c.execute(
            "SELECT l.id,l.url,l.name,l.size,l.status,l.error,l.plugin,l.package,l.linkorder FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? ORDER BY l.linkorder",
            (q,),
        )
        data = {}
        for r in self.c:
            data[r[0]] = {
                "id": r[0],
                "url": r[1],
                "name": r[2],
                "size": r[3],
                "format_size": format.size(r[3]),
                "status": r[4],
                "statusmsg": self.pyload.files.status_msg[r[4]],
                "error": r[5],
                "plugin": r[6],
                "package": r[7],
                "order": r[8],
            }

        return data

    @style.queue
    def get_all_packages(self, q):
        """
        return information about packages in queue q (only useful in get all data)

        q:
          0: queue
          1: packages

        format:

        {
            id: {'name': name ... 'links': {} }, ...
        }
        """
        self.c.execute(
            "SELECT p.id, p.name, p.folder, p.site, p.password, p.queue, p.packageorder, s.sizetotal, s.sizedone, s.linksdone, s.linkstotal \
            FROM packages p JOIN pstats s ON p.id = s.id \
            WHERE p.queue=? ORDER BY p.packageorder",
            str(q),
        )

        data = {}
        for r in self.c:
            data[r[0]] = {
                "id": r[0],
                "name": r[1],
                "folder": r[2],
                "site": r[3],
                "password": r[4],
                "queue": r[5],
                "order": r[6],
                "sizetotal": int(r[7]),
                "sizedone": r[8] if r[8] else 0,  #: these can be None
                "linksdone": r[9] if r[9] else 0,
                "linkstotal": r[10],
                "links": {},
            }

        return data

    @style.queue
    def get_link_data(self, id):
        """
        get link information as dict.
        """
        self.c.execute(
            "SELECT id,url,name,size,status,error,plugin,package,linkorder FROM links WHERE id=?",
            (str(id),),
        )
        r = self.c.fetchone()
        if not r:
            return None

        data = {
            r[0]: {
                "id": r[0],
                "url": r[1],
                "name": r[2],
                "size": r[3],
                "format_size": format.size(r[3]),
                "status": r[4],
                "statusmsg": self.pyload.files.status_msg[r[4]],
                "error": r[5],
                "plugin": r[6],
                "package": r[7],
                "order": r[8],
            }
        }

        return data

    @style.queue
    def get_package_data(self, id):
        """
        get data about links for a package.
        """
        self.c.execute(
            "SELECT id,url,name,size,status,error,plugin,package,linkorder FROM links WHERE package=? ORDER BY linkorder",
            (str(id),),
        )

        data = {}
        for r in self.c:
            data[r[0]] = {
                "id": r[0],
                "url": r[1],
                "name": r[2],
                "size": r[3],
                "format_size": format.size(r[3]),
                "status": r[4],
                "statusmsg": self.pyload.files.status_msg[r[4]],
                "error": r[5],
                "plugin": r[6],
                "package": r[7],
                "order": r[8],
            }

        return data

    @style.async_
    def update_link(self, f):
        self.c.execute(
            "UPDATE links SET url=?,name=?,size=?,status=?,error=?,package=? WHERE id=?",
            (f.url, f.name, f.size, f.status, f.error, str(f.packageid), str(f.id)),
        )

    @style.queue
    def update_package(self, p):
        self.c.execute(
            "UPDATE packages SET name=?,folder=?,site=?,password=?,queue=? WHERE id=?",
            (p.name, p.folder, p.site, p.password, p.queue, str(p.id)),
        )

    @style.queue
    def update_link_info(self, data):
        """
        data is list of tuples (name, size, status, url)
        """
        self.c.executemany(
            "UPDATE links SET name=?, size=?, status=? WHERE url=? AND status IN (1,2,3,14)",
            data,
        )
        ids = []
        statuses = "','".join(x[3] for x in data)
        self.c.execute(f"SELECT id FROM links WHERE url IN ('{statuses}')")
        for r in self.c:
            ids.append(int(r[0]))
        return ids

    @style.queue
    def reorder_package(self, p, position, no_move=False):
        if position == -1:
            position = self._next_package_order(p.queue)
        if not no_move:
            if p.order > position:
                self.c.execute(
                    "UPDATE packages SET packageorder=packageorder+1 WHERE packageorder >= ? AND packageorder < ? AND queue=? AND packageorder >= 0",
                    (position, p.order, p.queue),
                )
            elif p.order < position:
                self.c.execute(
                    "UPDATE packages SET packageorder=packageorder-1 WHERE packageorder <= ? AND packageorder > ? AND queue=? AND packageorder >= 0",
                    (position, p.order, p.queue),
                )

        self.c.execute(
            "UPDATE packages SET packageorder=? WHERE id=?", (position, str(p.id))
        )

    @style.queue
    def reorder_link(self, f, position):
        """
        reorder link with f as dict for pyfile.
        """
        if f["order"] > position:
            self.c.execute(
                "UPDATE links SET linkorder=linkorder+1 WHERE linkorder >= ? AND linkorder < ? AND package=?",
                (position, f["order"], f["package"]),
            )
        elif f["order"] < position:
            self.c.execute(
                "UPDATE links SET linkorder=linkorder-1 WHERE linkorder <= ? AND linkorder > ? AND package=?",
                (position, f["order"], f["package"]),
            )

        self.c.execute("UPDATE links SET linkorder=? WHERE id=?", (position, f["id"]))

    @style.queue
    def clear_package_order(self, p):
        self.c.execute("UPDATE packages SET packageorder=? WHERE id=?", (-1, str(p.id)))
        self.c.execute(
            "UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > ? AND queue=? AND id != ?",
            (p.order, p.queue, str(p.id)),
        )

    @style.async_
    def restart_file(self, id):
        self.c.execute('UPDATE links SET status=3,error="" WHERE id=?', (str(id),))

    @style.async_
    def restart_package(self, id):
        self.c.execute("UPDATE links SET status=3 WHERE package=?", (str(id),))

    @style.queue
    def get_package(self, id):
        """
        return package instance from id.
        """
        self.c.execute(
            "SELECT name,folder,site,password,queue,packageorder FROM packages WHERE id=?",
            (str(id),),
        )
        r = self.c.fetchone()
        if not r:
            return None
        return PyPackage(self.pyload.files, id, *r)

    # ----------------------------------------------------------------------
    @style.queue
    def get_file(self, id):
        """
        return link instance from id.
        """
        self.c.execute(
            "SELECT url, name, size, status, error, plugin, package, linkorder FROM links WHERE id=?",
            (str(id),),
        )
        r = self.c.fetchone()
        if not r:
            return None
        return PyFile(self.pyload.files, id, *r)

    @style.queue
    def get_job(self, occupied):
        """
        return pyfile ids, which are suitable for download and don't use an occupied
        plugin.
        """
        # TODO: improve this hardcoded method
        # plugins which are processed in collector
        pre = ("DLC", "TXT", "CCF", "RSDF")

        self.c.execute(
            f"""
            SELECT l.id FROM links as l
            INNER JOIN packages as p ON l.package=p.id
            WHERE ((p.queue=1 AND l.plugin NOT IN ({",".join("?" * len(occupied))})) OR l.plugin IN ({",".join("?" * len(pre))})) AND l.status IN (2,3,14)
            ORDER BY p.packageorder ASC, l.linkorder ASC
            LIMIT 5
            """,
            occupied + pre,
        )

        return [x[0] for x in self.c]

    @style.queue
    def get_plugin_job(self, plugins):
        """
        returns pyfile ids with suited plugins.
        """
        self.c.execute(
            f"""
            SELECT l.id FROM links as l
            INNER JOIN packages as p ON l.package=p.id
            WHERE l.plugin IN ({",".join("?" * len(plugins))}) AND l.status IN (2,3,14)
            ORDER BY p.packageorder ASC, l.linkorder ASC LIMIT 5
            """,
            plugins,
        )

        return [x[0] for x in self.c]

    @style.queue
    def get_unfinished(self, pid):
        """
        return list of max length 3 ids with pyfiles in package not finished or
        processed.
        """
        self.c.execute(
            "SELECT id FROM links WHERE package=? AND status NOT IN (0, 4, 13) LIMIT 3",
            (str(pid),),
        )
        return [r[0] for r in self.c]

    @style.queue
    def delete_finished(self):
        self.c.execute("DELETE FROM links WHERE status IN (0,4)")
        self.c.execute(
            "DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE packages.id=links.package)"
        )

    @style.queue
    def restart_failed(self):
        self.c.execute("UPDATE links SET status=3,error='' WHERE status IN (6, 8, 9)")

    @style.queue
    def find_duplicates(self, id, folder, filename):
        """
        checks if filename exists with different id and same package.
        """
        self.c.execute(
            "SELECT l.plugin FROM links as l INNER JOIN packages as p ON l.package=p.id AND p.folder=? WHERE l.id!=? AND l.status=0 AND l.name=?",
            (folder, id, filename),
        )
        return self.c.fetchone()

    @style.queue
    def purge_links(self):
        self.c.execute("DELETE FROM links;")
        self.c.execute("DELETE FROM packages;")
