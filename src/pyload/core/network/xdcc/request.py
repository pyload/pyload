# -*- coding: utf-8 -*-

import errno
import os
import select
import socket
import ssl
import struct
import time

from ..exceptions import Abort, Fail


class XDCCRequest:
    def __init__(self, bucket=None, options=None):
        options = options or {}
        self.proxies = options.get("proxies", {})
        self.bucket = bucket

        self.fh = None
        self.dcc_sock = None

        self.filesize = 0
        self.received = 0
        self.speeds = [0, 0, 0]

        self.sleep = 0.000
        self.last_recv_size = 0
        self.send_64bits_ack = False

        self.abort = False

        self.status_notify = None

    def create_socket(self):
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
        # acknowledge data by sending number of received bytes
        try:
            self.dcc_sock.send(
                struct.pack("!Q" if self.send_64bits_ack else "!I", self.received)
            )

        except (socket.error, ssl.SSLError):
            pass

    def download(self, ip, port, filename, status_notify=None, resume=None, use_ssl=False):
        self.status_notify = status_notify
        self.send_64bits_ack = not self.filesize < 1 << 32

        chunk_name = filename + ".chunk0"

        if resume and os.path.exists(chunk_name):
            self.fh = open(chunk_name, mode="ab")
            resume_position = self.fh.tell()
            if not resume_position:
                resume_position = os.stat(chunk_name).st_size

            resume_position = resume(resume_position)
            self.fh.truncate(resume_position)
            self.received = resume_position

        else:
            self.fh = open(chunk_name, mode="wb")

        self.dcc_sock = self.create_socket()

        try:
            self.dcc_sock.connect((ip, port))

            # Wrap socket with SSL if enabled
            if use_ssl:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self.dcc_sock = ssl_context.wrap_socket(self.dcc_sock, server_hostname=ip)
        except (socket.error, ssl.SSLError) as exc:
            raise Fail("Unable to connect to server") from exc

        self.dcc_sock.setblocking(False)

        try:
            self._download_loop()
        finally:
            self.dcc_sock.close()
            self.fh.close()

        os.rename(chunk_name, filename)

        return filename

    def download_passive(self, listen_port, filename, passive_initiate_cb, dcc_token, status_notify=None, listen_host=None, resume=None, listen_timeout=120):
        self.status_notify = status_notify
        self.send_64bits_ack = not self.filesize < 1 << 32

        chunk_name = filename + ".chunk0"

        if resume and os.path.exists(chunk_name):
            self.fh = open(chunk_name, mode="ab")
            resume_position = self.fh.tell()
            if not resume_position:
                resume_position = os.stat(chunk_name).st_size
            resume_position = resume(resume_position)
            self.fh.truncate(resume_position)
            self.received = resume_position
        else:
            self.fh = open(chunk_name, mode="wb")

        # Send CTCP DCC SEND reply with our ip/port
        passive_initiate_cb(dcc_token)

        try:
            # Setup listening socket
            listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_sock.bind((listen_host or "", listen_port))
            listen_sock.listen(1)

            # Accept incoming connection
            conn = None
            listen_sock.settimeout(listen_timeout)
            conn, _ = listen_sock.accept()
        except socket.timeout as exc:
            self.fh.close()
            raise Fail("Passive DCC connection timeout") from exc

        finally:
            listen_sock.close()

        self.dcc_sock = conn
        self.dcc_sock.setblocking(False)

        try:
            self._download_loop()
        finally:
            self.dcc_sock.close()
            self.fh.close()

        os.rename(chunk_name, filename)

        return filename

    def abort_downloads(self):
        self.abort = True

    @property
    def size(self):
        return self.filesize

    @property
    def arrived(self):
        return self.received

    @property
    def speed(self):
        speeds = [x for x in self.speeds if x]
        return sum(speeds) // len(speeds)

    @property
    def percent(self):
        if not self.filesize:
            return 0
        return (self.received * 100) // self.filesize

    def close(self):
        pass

    def _update_progress(self):
        if self.status_notify:
            self.status_notify({"progress": self.percent})

    def _download_loop(self):
        # recv loop for dcc socket
        last_update = time.time()
        num_recv_len = 0
        recv_list = [self.dcc_sock]

        while True:
            if self.abort:
                raise Abort

            fdset = select.select(recv_list, [], [], 0.1)
            if self.dcc_sock in fdset[0]:
                try:
                    data = self.dcc_sock.recv(16384)

                except socket.error as exc:
                    if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                        continue

                    else:
                        raise

                except ssl.SSLError as exc:
                    # Handle SSL-specific errors
                    if exc.errno in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                        continue
                    else:
                        raise

                data_len = len(data)
                if (
                    data_len == 0
                    or self.received + data_len > self.filesize > 0
                ):
                    break

                num_recv_len += data_len

                self._write_func(data)
                self._send_ack()

            now = time.time()
            timespan = now - last_update
            if timespan > 1:
                # calc speed once per second, averaging over 3 seconds
                self.speeds[2] = self.speeds[1]
                self.speeds[1] = self.speeds[0]
                self.speeds[0] = num_recv_len // timespan

                num_recv_len = 0
                last_update = now

                self._update_progress()
