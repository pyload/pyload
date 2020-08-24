# -*- coding: utf-8 -*-


class style:
    db = None

    @classmethod
    def set_db(cls, db):
        cls.db = db

    @classmethod
    def inner(cls, fn):
        @staticmethod
        def x(*args, **kwargs):
            return fn(cls.db, *args, **kwargs)

        return x

    @classmethod
    def queue(cls, fn):
        @staticmethod
        def x(*args, **kwargs):
            return cls.db.queue(fn, *args, **kwargs)

        return x

    @classmethod
    def async_(cls, fn):
        @staticmethod
        def x(*args, **kwargs):
            return cls.db.async_(fn, *args, **kwargs)

        return x
