#!/usr/bin/env python
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
    @author: mkaay
"""
from threading import Thread, Event
from shutil import move

from Queue import Queue
from traceback import print_exc

from module.utils.fs import chmod, exists, remove

try:
    from pysqlite2 import dbapi2 as sqlite3
except:
    import sqlite3

DB = None
DB_VERSION = 5

def set_DB(db):
    global DB
    DB = db


def queue(f):
    @staticmethod
    def x(*args, **kwargs):
        if DB:
            return DB.queue(f, *args, **kwargs)

    return x


def async(f):
    @staticmethod
    def x(*args, **kwargs):
        if DB:
            return DB.async(f, *args, **kwargs)

    return x


def inner(f):
    @staticmethod
    def x(*args, **kwargs):
        if DB:
            return f(DB, *args, **kwargs)

    return x


class DatabaseMethods:
    # stubs for autocompletion
    core = None
    manager = None
    conn = None
    c = None

    @classmethod
    def register(cls):
        DatabaseBackend.registerSub(cls)


class DatabaseJob():
    def __init__(self, f, *args, **kwargs):
        self.done = Event()

        self.f = f
        self.args = args
        self.kwargs = kwargs

        self.result = None
        self.exception = False

    #        import inspect
    #        self.frame = inspect.currentframe()

    def __repr__(self):
        from os.path import basename

        frame = self.frame.f_back
        output = ""
        for i in range(5):
            output += "\t%s:%s, %s\n" % (basename(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name)
            frame = frame.f_back
        del frame
        del self.frame

        return "DataBase Job %s:%s\n%sResult: %s" % (self.f.__name__, self.args[1:], output, self.result)

    def processJob(self):
        try:
            self.result = self.f(*self.args, **self.kwargs)
        except Exception, e:
            print_exc()
            try:
                print "Database Error @", self.f.__name__, self.args[1:], self.kwargs, e
            except:
                pass

            self.exception = e
        finally:
            self.done.set()

    def wait(self):
        self.done.wait()


class DatabaseBackend(Thread):
    subs = []

    DB_FILE = "pyload.db"
    VERSION_FILE = "db.version"

    def __init__(self, core):
        Thread.__init__(self)
        self.setDaemon(True)
        self.core = core
        self.manager = None # set later
        self.running = Event()

        self.jobs = Queue()

        set_DB(self)

    def setup(self):

        self.start()
        self.running.wait()

    def init(self):
        """main loop, which executes commands"""

        version = self._checkVersion()

        self.conn = sqlite3.connect(self.DB_FILE)
        chmod(self.DB_FILE, 0600)

        self.c = self.conn.cursor()

        if version is not None and version < DB_VERSION:
            success = self._convertDB(version)

            # delete database
            if not success:
                self.c.close()
                self.conn.close()

                try:
                    self.manager.core.log.warning(_("File database was deleted due to incompatible version."))
                except:
                    print "File database was deleted due to incompatible version."

                remove(self.VERSION_FILE)
                move(self.DB_FILE, self.DB_FILE + ".backup")
                f = open(self.VERSION_FILE, "wb")
                f.write(str(DB_VERSION))
                f.close()

                self.conn = sqlite3.connect(self.DB_FILE)
                chmod(self.DB_FILE, 0600)
                self.c = self.conn.cursor()

        self._createTables()
        self.conn.commit()


    def run(self):
        try:
            self.init()
        finally:
            self.running.set()

        while True:
            j = self.jobs.get()
            if j == "quit":
                self.c.close()
                self.conn.close()
                break
            j.processJob()


    def shutdown(self):
        self.running.clear()
        self._shutdown()

    @queue
    def _shutdown(self):
        self.conn.commit()
        self.jobs.put("quit")

    def _checkVersion(self):
        """ get db version"""
        if not exists(self.VERSION_FILE):
            f = open(self.VERSION_FILE, "wb")
            f.write(str(DB_VERSION))
            f.close()
            return

        f = open(self.VERSION_FILE, "rb")
        v = int(f.read().strip())
        f.close()

        return v

    def _convertDB(self, v):
        try:
            return getattr(self, "_convertV%i" % v)()
        except:
            return False

    #--convert scripts start

    def _convertV5(self):
        return False

    #--convert scripts end

    def _createTables(self):
        """create tables for database"""

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "packages" ('
            '"pid" INTEGER PRIMARY KEY AUTOINCREMENT, '
            '"name" TEXT NOT NULL, '
            '"folder" TEXT DEFAULT "" NOT NULL, '
            '"site" TEXT DEFAULT "" NOT NULL, '
            '"comment" TEXT DEFAULT "" NOT NULL, '
            '"password" TEXT DEFAULT "" NOT NULL, '
            '"added" INTEGER DEFAULT 0 NOT NULL,' # set by trigger
            '"status" INTEGER DEFAULT 0 NOT NULL,'
            '"packageorder" INTEGER DEFAULT -1 NOT NULL,' #incremented by trigger
            '"root" INTEGER DEFAULT -1 NOT NULL,'
            'CHECK (root != pid) '
            ')'
        )

        self.c.execute(
            'CREATE TRIGGER IF NOT EXISTS "insert_package" AFTER INSERT ON "packages"'
            'BEGIN '
            'UPDATE packages SET added = strftime("%s", "now"), '
            'packageorder = (SELECT max(p.packageorder) + 1 FROM packages p WHERE p.root=new.root) '
            'WHERE rowid = new.rowid;'
            'END'
        )

        self.c.execute(
            'CREATE TRIGGER IF NOT EXISTS "delete_package" AFTER DELETE ON "packages"'
            'BEGIN '
            'DELETE FROM files WHERE package = old.pid;'
            'UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > old.packageorder AND root=old.pid;'
            'END'
        )

        self.c.execute('CREATE INDEX IF NOT EXISTS "root_index" ON packages(root)')

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "files" ('
            '"fid" INTEGER PRIMARY KEY AUTOINCREMENT, '
            '"name" TEXT NOT NULL, '
            '"size" INTEGER DEFAULT 0 NOT NULL, '
            '"status" INTEGER DEFAULT 0 NOT NULL, '
            '"media" INTEGER DEFAULT 1 NOT NULL,'
            '"added" INTEGER DEFAULT 0 NOT NULL,'
            '"fileorder" INTEGER DEFAULT -1 NOT NULL, '
            '"url" TEXT DEFAULT "" NOT NULL, '
            '"plugin" TEXT DEFAULT "" NOT NULL, '
            '"hash" TEXT DEFAULT "" NOT NULL, '
            '"dlstatus" INTEGER DEFAULT 0 NOT NULL, '
            '"error" TEXT DEFAULT "" NOT NULL, '
            '"package" INTEGER NOT NULL, '
            'FOREIGN KEY(package) REFERENCES packages(id)'
            ')'
        )

        self.c.execute('CREATE INDEX IF NOT EXISTS "package_index" ON files(package)')

        self.c.execute(
            'CREATE TRIGGER IF NOT EXISTS "insert_file" AFTER INSERT ON "files"'
            'BEGIN '
            'UPDATE files SET added = strftime("%s", "now"), '
            'fileorder = (SELECT max(f.fileorder) + 1 FROM files f WHERE f.package=new.package) '
            'WHERE rowid = new.rowid;'
            'END'
        )

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "collector" ('
            '"url" TEXT NOT NULL, '
            '"name" TEXT NOT NULL, '
            '"plugin" TEXT DEFAULT "BasePlugin" NOT NULL, '
            '"size" INTEGER DEFAULT 0 NOT NULL, '
            '"status" INTEGER DEFAULT 3 NOT NULL, '
            '"packagename" TEXT DEFAULT "" NOT NULL, '
            'PRIMARY KEY (url, packagename) ON CONFLICT REPLACE'
            ') '
        )

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "storage" ('
            '"identifier" TEXT NOT NULL, '
            '"key" TEXT NOT NULL, '
            '"value" TEXT DEFAULT "", '
            'PRIMARY KEY (identifier, key) ON CONFLICT REPLACE'
            ')'
        )

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "users" ('
            '"name" TEXT PRIMARY KEY NOT NULL, '
            '"email" TEXT DEFAULT "" NOT NULL, '
            '"password" TEXT NOT NULL, '
            '"role" INTEGER DEFAULT 0 NOT NULL, '
            '"permission" INTEGER DEFAULT 0 NOT NULL, '
            '"folder" TEXT DEFAULT "" NOT NULL, '
            '"template" TEXT DEFAULT "default" NOT NULL'
            ')'
        )

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "accounts" ('
            '"plugin" TEXT NOT NULL, '
            '"loginname" TEXT NOT NULL, '
            '"activated" INTEGER DEFAULT 1, '
            '"password" TEXT DEFAULT "", '
            '"options" TEXT DEFAULT "", '
#            '"user" TEXT NOT NULL, '
#            'FOREIGN KEY(user) REFERENCES users(name)'
            'PRIMARY KEY (plugin, loginname) ON CONFLICT REPLACE'
            ')'
        )

        #try to lower ids
        self.c.execute('SELECT max(fid) FROM files')
        fid = self.c.fetchone()[0]
        fid = int(fid) if fid else 0
        self.c.execute('UPDATE SQLITE_SEQUENCE SET seq=? WHERE name=?', (fid, "files"))

        self.c.execute('SELECT max(pid) FROM packages')
        pid = self.c.fetchone()[0]
        pid = int(pid) if pid else 0
        self.c.execute('UPDATE SQLITE_SEQUENCE SET seq=? WHERE name=?', (pid, "packages"))

        self.c.execute('VACUUM')


    def createCursor(self):
        return self.conn.cursor()

    @async
    def commit(self):
        self.conn.commit()

    @queue
    def syncSave(self):
        self.conn.commit()

    @async
    def rollback(self):
        self.conn.rollback()

    def async(self, f, *args, **kwargs):
        args = (self, ) + args
        job = DatabaseJob(f, *args, **kwargs)
        self.jobs.put(job)

    def queue(self, f, *args, **kwargs):
        args = (self, ) + args
        job = DatabaseJob(f, *args, **kwargs)
        self.jobs.put(job)
        # only wait when db is running
        if self.running.isSet(): job.wait()
        return job.result

    @classmethod
    def registerSub(cls, klass):
        cls.subs.append(klass)

    @classmethod
    def unregisterSub(cls, klass):
        cls.subs.remove(klass)

    def __getattr__(self, attr):
        for sub in DatabaseBackend.subs:
            if hasattr(sub, attr):
                return getattr(sub, attr)
        raise AttributeError(attr)

if __name__ == "__main__":
    db = DatabaseBackend()
    db.setup()

    class Test():
        @queue
        def insert(db):
            c = db.createCursor()
            for i in range(1000):
                c.execute("INSERT INTO storage (identifier, key, value) VALUES (?, ?, ?)", ("foo", i, "bar"))

        @async
        def insert2(db):
            c = db.createCursor()
            for i in range(1000 * 1000):
                c.execute("INSERT INTO storage (identifier, key, value) VALUES (?, ?, ?)", ("foo", i, "bar"))

        @queue
        def select(db):
            c = db.createCursor()
            for i in range(10):
                res = c.execute("SELECT value FROM storage WHERE identifier=? AND key=?", ("foo", i))
                print res.fetchone()

        @queue
        def error(db):
            c = db.createCursor()
            print "a"
            c.execute("SELECT myerror FROM storage WHERE identifier=? AND key=?", ("foo", i))
            print "e"

    db.registerSub(Test)
    from time import time

    start = time()
    for i in range(100):
        db.insert()
    end = time()
    print end - start

    start = time()
    db.insert2()
    end = time()
    print end - start

    db.error()

