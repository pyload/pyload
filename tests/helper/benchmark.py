# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time
from builtins import object, range, str

from future import standard_library

standard_library.install_aliases()


class BenchmarkTest(object):

    bench = []
    results = {}

    @classmethod
    def timestamp(cls, name, a):
        t = time.time()
        res = cls.results.get(name, [])
        res.append((t - a) * 1000)
        cls.results[name] = res

    @classmethod
    def benchmark(cls, n=1):

        print("Benchmarking {0}".format(cls.__name__))
        print()

        for i in range(n):
            cls.collect_results()

        if "setUpClass" in cls.results:
            cls.bench.insert(0, "setUpClass")

        if "tearDownClass" in cls.results:
            cls.bench.append("tearDownClass")

        length = str(max(len(k) for k in cls.bench) + 1)
        total = 0

        for k in cls.bench:
            v = cls.results[k]

            if len(v) > 1:
                print(("{0:" + length + "} {1} | average: {2:.2f} ms").format(
                    k, ", ".join("{0:.2f}".format(x)
                                 for x in v), sum(v) // len(v)
                ))
                total += sum(v) // len(v)
            else:
                print(("{0:" + length + "}: {1:.2f} ms").format(k, v[0]))
                total += v[0]

        print("\ntotal: {0:.2f} ms".format(total))

    @classmethod
    def collect_results(cls):
        if hasattr(cls, "setUpClass"):
            a = time.time()
            cls.setUpClass()
            cls.timestamp("setUpClass", a)

        obj = cls()

        for fname in cls.bench:
            a = time.time()
            getattr(obj, "test_{0}".format(fname))()
            cls.timestamp(fname, a)

        if hasattr(cls, "tearDownClass"):
            a = time.time()
            cls.tearDownClass()
            cls.timestamp("tearDownClass", a)
