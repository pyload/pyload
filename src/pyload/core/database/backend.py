# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

from __future__ import absolute_import, unicode_literals

import os
import shutil
from builtins import int, object, str
from queue import Queue
from traceback import print_exc

from future import standard_library

from pyload.utils.fs import lopen, remove
from pyload.utils.layer.safethreading import Event, Thread

standard_library.install_aliases()


try:
    from pysqlite2 import dbapi2 as sqlite3
except Exception:
    import sqlite3

DB = None
DB_VERSION = 7


def set_db(db):
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


class DatabaseMethods(object):

    # stubs for autocompletion
    core = None
    manager = None
    conn = None
    c = None

    @classmethod
    def register(cls):
        DatabaseBackend.register_sub(cls)


class DatabaseJob(object):

    def __init__(self, func, *args, **kwargs):
        self.done = Event()

        self.func = func
        self.args = args
        self.kwgs = kwargs

        self.result = None
        self.exception = False

        # import inspect
        # self.frame = inspect.currentframe()

    def __repr__(self):
        # frame = self.frame.f_back
        output = ""
        # for i in range(5):
        # output += "\t{0}:{1}, {2}\n".format(
        # os.path.basename(
        # frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name)
        # frame = frame.f_back
        # del frame
        # del self.frame
        return "DataBase Job {0}:{1}{2}{3}Result: {4}".format(
            self.func.__name__, self.args[1:], os.linesep, output, self.result)

    def process_job(self):
        try:
            self.result = self.func(*self.args, **self.kwgs)
        except Exception as e:
            print_exc()
            try:
                print("Database Error @", self.func.__name__,
                      self.args[1:], self.kwgs, str(e))
            except Exception:
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
        self.__pyload = core
        self._ = core._
        self.__manager = None  # set later
        self.error = None
        self.__running = Event()

        self.jobs = Queue()

        set_db(self)

    @property
    def pyload_core(self):
        return self.__pyload

    @property
    def running(self):
        return self.__running.is_set()

    def setup(self):
        """
        *MUST* be called before db can be used !.
        """
        self.start()
        self.__running.wait()

    def init(self):
        """
        Main loop, which executes commands.
        """
        version = self._check_version()

        self.conn = sqlite3.connect(self.DB_FILE)
        os.chmod(self.DB_FILE, 0o600)

        self.c = self.conn.cursor()

        if version is not None and version < DB_VERSION:
            success = self._convert_db(version)

            # delete database
            if not success:
                self.c.close()
                self.conn.close()

                try:
                    self.pyload_core.log.warning(
                        self._("Database was deleted "
                               "due to incompatible version"))
                except Exception:
                    print("Database was deleted due to incompatible version")

                remove(self.VERSION_FILE)
                shutil.move(self.DB_FILE, self.DB_FILE + ".bak")
                with lopen(self.VERSION_FILE, mode='wb') as fp:
                    fp.write(str(DB_VERSION))

                self.conn = sqlite3.connect(self.DB_FILE)
                os.chmod(self.DB_FILE, 0o600)
                self.c = self.conn.cursor()

        self._create_tables()
        self.conn.commit()

    def run(self):
        try:
            self.init()
        except Exception as e:
            self.error = e
        finally:
            self.__running.set()

        while True:
            j = self.jobs.get()
            if j == "quit":
                self.c.close()
                self.conn.commit()
                self.conn.close()
                self.closing.set()
                break
            j.process_job()

    # TODO: Recheck...
    def shutdown(self):
        self.__running.clear()
        self.closing = Event()
        self.jobs.put("quit")
        self.closing.wait(1)

    def _check_version(self):
        """
        Get db version.
        """
        try:
            with lopen(self.VERSION_FILE, mode='rb') as fp:
                v = int(fp.read().strip())
        except IOError:
            with lopen(self.VERSION_FILE, mode='wb') as fp:
                fp.write(str(DB_VERSION))
            return None
        return v

    def _convert_db(self, v):
        try:
            return getattr(self, "_convertV{0:d}".format(v))()
        except Exception:
            return False

    # -- convert scripts start --

    def _convert_v6(self):
        return False

    # -- convert scripts end --

    def _create_tables(self):
        """
        Create tables for database.
        """
        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "packages" ('
            '"pid" INTEGER PRIMARY KEY AUTOINCREMENT, '
            '"name" TEXT NOT NULL, '
            '"folder" TEXT DEFAULT "" NOT NULL, '
            '"site" TEXT DEFAULT "" NOT NULL, '
            '"comment" TEXT DEFAULT "" NOT NULL, '
            '"password" TEXT DEFAULT "" NOT NULL, '
            '"added" INTEGER DEFAULT 0 NOT NULL,'  # set by trigger
            '"status" INTEGER DEFAULT 0 NOT NULL,'
            '"tags" TEXT DEFAULT "" NOT NULL,'
            '"shared" INTEGER DEFAULT 0 NOT NULL,'
            '"packageorder" INTEGER DEFAULT -1 NOT NULL,'  # inc by trigger
            '"root" INTEGER DEFAULT -1 NOT NULL, '
            '"owner" INTEGER NOT NULL, '
            'FOREIGN KEY(owner) REFERENCES users(uid), '
            'CHECK (root != pid)'
            ')'
        )

        self.c.execute(
            'CREATE TRIGGER IF NOT EXISTS "insert_package" '
            'AFTER INSERT ON "packages"'
            'BEGIN '
            'UPDATE packages SET added = strftime("%s", "now"), '
            'packageorder = (SELECT max(p.packageorder) + 1 FROM '
            'packages p WHERE p.root=new.root) '
            'WHERE rowid = new.rowid;'
            'END')

        self.c.execute(
            'CREATE TRIGGER IF NOT EXISTS "delete_package" '
            'AFTER DELETE ON "packages"'
            'BEGIN '
            'DELETE FROM files WHERE package = old.pid;'
            'UPDATE packages SET packageorder=packageorder-1 '
            'WHERE packageorder > old.packageorder AND root=old.pid;'
            'END')
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "package_index" ON '
            'packages(root, owner)')
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "package_owner" ON packages(owner)')

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
            '"owner" INTEGER NOT NULL, '
            'FOREIGN KEY(owner) REFERENCES users(uid), '
            'FOREIGN KEY(package) REFERENCES packages(id)'
            ')'
        )
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "file_index" ON files(package, owner)')
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "file_owner" ON files(owner)')
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "file_plugin" ON files(plugin)')

        self.c.execute(
            'CREATE TRIGGER IF NOT EXISTS "insert_file" '
            'AFTER INSERT ON "files"'
            'BEGIN '
            'UPDATE files SET added = strftime("%s", "now"), '
            'fileorder = (SELECT max(f.fileorder) + 1 FROM files f '
            'WHERE f.package=new.package) '
            'WHERE rowid = new.rowid;'
            'END')

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "collector" ('
            '"owner" INTEGER NOT NULL, '
            '"data" TEXT NOT NULL, '
            'FOREIGN KEY(owner) REFERENCES users(uid), '
            'PRIMARY KEY(owner) ON CONFLICT REPLACE'
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
            '"uid" INTEGER PRIMARY KEY AUTOINCREMENT, '
            '"name" TEXT NOT NULL UNIQUE, '
            '"email" TEXT DEFAULT "" NOT NULL, '
            '"password" TEXT NOT NULL, '
            '"role" INTEGER DEFAULT 0 NOT NULL, '
            '"permission" INTEGER DEFAULT 0 NOT NULL, '
            '"folder" TEXT DEFAULT "" NOT NULL, '
            '"traffic" INTEGER DEFAULT -1 NOT NULL, '
            '"dllimit" INTEGER DEFAULT -1 NOT NULL, '
            '"dlquota" TEXT DEFAULT "" NOT NULL, '
            '"hddquota" INTEGER DEFAULT -1 NOT NULL, '
            '"template" TEXT DEFAULT "default" NOT NULL, '
            '"user" INTEGER DEFAULT -1 NOT NULL, '  # set by trigger to self
            'FOREIGN KEY(user) REFERENCES users(uid)'
            ')'
        )
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "username_index" ON users(name)')

        self.c.execute(
            'CREATE TRIGGER IF NOT EXISTS "insert_user" AFTER '
            'INSERT ON "users"'
            'BEGIN '
            'UPDATE users SET user = new.uid, folder=new.name '
            'WHERE rowid = new.rowid;'
            'END')

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "settings" ('
            '"plugin" TEXT NOT NULL, '
            '"user" INTEGER DEFAULT -1 NOT NULL, '
            '"config" TEXT NOT NULL, '
            'FOREIGN KEY(user) REFERENCES users(uid), '
            'PRIMARY KEY (plugin, user) ON CONFLICT REPLACE'
            ')'
        )

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "accounts" ('
            '"aid" INTEGER PRIMARY KEY AUTOINCREMENT, '
            '"plugin" TEXT NOT NULL, '
            '"loginname" TEXT NOT NULL, '
            '"owner" INTEGER NOT NULL, '
            '"activated" INTEGER NOT NULL DEFAULT 1, '
            '"password" TEXT DEFAULT "", '
            '"shared" INTEGER NOT NULL DEFAULT 0, '
            '"options" TEXT DEFAULT "", '
            'FOREIGN KEY(owner) REFERENCES users(uid)'
            ')'
        )

        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "accounts_login" ON '
            'accounts(plugin, loginname)')

        self.c.execute(
            'CREATE TABLE IF NOT EXISTS "stats" ('
            '"id" INTEGER PRIMARY KEY AUTOINCREMENT, '
            '"user" INTEGER NOT NULL, '
            '"plugin" TEXT NOT NULL, '
            '"time" INTEGER NOT NULL, '
            '"premium" INTEGER DEFAULT 0 NOT NULL, '
            '"amount" INTEGER DEFAULT 0 NOT NULL, '
            'FOREIGN KEY(user) REFERENCES users(uid)'
            ')'
        )
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS "stats_time" ON stats(user, time)')

        # try to lower ids
        self.c.execute('SELECT max(fid) FROM files')
        fid = self.c.fetchone()[0]
        fid = int(fid) if fid else 0
        self.c.execute(
            'UPDATE SQLITE_SEQUENCE SET seq=? WHERE name=?', (fid, "files"))

        self.c.execute('SELECT max(pid) FROM packages')
        pid = self.c.fetchone()[0]
        pid = int(pid) if pid else 0
        self.c.execute(
            'UPDATE SQLITE_SEQUENCE SET seq=? WHERE name=?', (pid, "packages"))

        self.c.execute('VACUUM')

    def create_cursor(self):
        return self.conn.cursor()

    @async
    def commit(self):
        self.conn.commit()

    @queue
    def sync_save(self):
        self.conn.commit()

    @async
    def rollback(self):
        self.conn.rollback()

    def async(self, f, *args, **kwargs):
        args = (self,) + args
        job = DatabaseJob(f, *args, **kwargs)
        self.jobs.put(job)

    def queue(self, f, *args, **kwargs):
        # Raise previous error of initialization
        if isinstance(self.error, Exception):
            raise self.error
        args = (self,) + args
        job = DatabaseJob(f, *args, **kwargs)
        self.jobs.put(job)

        # only wait when db is running
        if self.running:
            job.wait()
        return job.result

    @classmethod
    def register_sub(cls, klass):
        cls.subs.append(klass)

    @classmethod
    def unregister_sub(cls, klass):
        cls.subs.remove(klass)

    def __getattr__(self, attr):
        for sub in DatabaseBackend.subs:
            if hasattr(sub, attr):
                return getattr(sub, attr)
        raise AttributeError(attr)
