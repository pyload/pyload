#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

    @authors: jeix, GammaC0de
"""

import errno
import os
import select
import socket
import struct
import time

from module.plugins.Plugin import Abort


class XDCCRequest():
    def __init__(self, bucket=None, options={}):
        self.proxies = options.get('proxies', {})
        self.bucket  = bucket

        self.fh      = None
        self.dccsock = None

        self.filesize = 0
        self.received = 0
        self.speeds   = [0.0, 0.0, 0.0]

        self.sleep = 0.000
        self.last_recv_size = 0
        self.send_64bits_ack = False

        self.abort = False

        self.progressNotify = None


    def createSocket(self):
        # proxytype = None
        # proxy = None
        # if self.proxies.has_key("socks5"):
        # proxytype = socks.PROXY_TYPE_SOCKS5
        # proxy = self.proxies["socks5"]
        # elif self.proxies.has_key("socks4"):
        # proxytype = socks.PROXY_TYPE_SOCKS4
        # proxy = self.proxies["socks4"]
        # if proxytype:
        # sock = socks.socksocket()
        # t = _parse_proxy(proxy)
        # sock.setproxy(proxytype, addr=t[3].split(":")[0], port=int(t[3].split(":")[1]), username=t[1], password=t[2])
        # else:
        # sock = socket.socket()
        # return sock

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16384)

        return sock


    def _write_func(self, buf):
        size = len(buf)

        self.received += size

        self.fh.write(buf)

        if self.bucket:
            time.sleep(self.bucket.consumed(size))

        else:
            # Avoid small buffers, increasing sleep time slowly if buffer size gets smaller
            # otherwise reduce sleep time percentequal (values are based on tests)
            # So in general cpu time is saved without reducing bandwidth too much

            if size < self.last_recv_size:
                self.sleep += 0.002
            else:
                self.sleep *= 0.7

            self.last_recv_size = size

            time.sleep(self.sleep)


    def _send_ack(self):
        # acknowledge data by sending number of recceived bytes
        try:
            self.dccsock.send(struct.pack('!Q' if self.send_64bits_ack else '!I', self.received))

        except socket.error:
            pass


    def download(self, ip, port, filename, progressNotify=None, resume=None):
        self.progressNotify = progressNotify
        self.send_64bits_ack = False if self.filesize < 1 << 32 else True

        chunk_name = filename + ".chunk0"

        if resume and os.path.exists(chunk_name):
            self.fh = open(chunk_name, "ab")
            resume_position = self.fh.tell()
            if not resume_position:
                resume_position = os.stat(chunk_name).st_size

            resume_position = resume(resume_position)
            self.fh.truncate(resume_position)
            self.received = resume_position

        else:
            self.fh = open(chunk_name, "wb")

        lastUpdate = time.time()
        cumRecvLen = 0

        self.dccsock = self.createSocket()

        recv_list = [self.dccsock]
        self.dccsock.connect((ip, port))
        self.dccsock.setblocking(0)

        # recv loop for dcc socket
        while True:
            if self.abort:
                self.dccsock.close()
                self.fh.close()
                raise Abort()

            fdset = select.select(recv_list, [], [], 0.1)
            if self.dccsock in fdset[0]:
                try:
                    data = self.dccsock.recv(16384)

                except socket.error, e:
                    if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                        continue

                    else:
                        raise

                data_len = len(data)
                if data_len == 0 or self.filesize and self.received + data_len > self.filesize:
                    break

                cumRecvLen += data_len

                self._write_func(data)
                self._send_ack()

            now = time.time()
            timespan = now - lastUpdate
            if timespan > 1:
                # calc speed once per second, averaging over 3 seconds
                self.speeds[2] = self.speeds[1]
                self.speeds[1] = self.speeds[0]
                self.speeds[0] = float(cumRecvLen) / timespan

                cumRecvLen = 0
                lastUpdate = now

                self.updateProgress()

        self.dccsock.close()
        self.fh.close()

        os.rename(chunk_name, filename)

        return filename


    def abortDownloads(self):
        self.abort = True


    def updateProgress(self):
        if self.progressNotify:
            self.progressNotify(self.percent)


    @property
    def size(self):
        return self.filesize


    @property
    def arrived(self):
        return self.received


    @property
    def speed(self):
        speeds = [x for x in self.speeds if x]
        return sum(speeds) / len(speeds)


    @property
    def percent(self):
        if not self.filesize: return 0
        return (self.received * 100) / self.filesize


    def close(self):
        pass
