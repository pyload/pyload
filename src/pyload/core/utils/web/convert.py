# -*- coding: utf-8 -*-

import socket

# import idna

from ..convert import to_str


# def splitaddress(address):
#     try:
#         address = to_str(idna.encode(address))
#     except (AttributeError, idna.IDNAError):
#         pass
#     sep = "]:" if address.split(":", 2)[2:] else ":"
#     parts = address.rsplit(sep, 1)
#     try:
#         addr, port = parts
#         port = int(port)
#     except ValueError:
#         addr = parts[0]
#         port = None
#     return addr, port


# def host_to_ip(hostname):
#     _, _, ipaddrlist = socket.gethostbyname_ex(hostname)
#     return ipaddrlist


# def ip_to_host(ipaddress):
#     hostname, aliaslist, _ = socket.gethostbyaddr(ipaddress)
#     return [hostname] + aliaslist


# def socket_to_endpoint(socket):
#     ip, port = splitaddress(socket)
#     host = ip_to_host(ip)
#     port = int(port)
#     return f"{host}:{port}"


# def endpoint_to_socket(endpoint):
#     host, port = splitaddress(endpoint)
#     addrinfo = socket.getaddrinfo(host, int(port))
#     return addrinfo[0][-1][:2], addrinfo[1][-1][:2]


# def code_to_status(code):
# code = int(code)
# if code < 400:
# status = 'online'
# elif code < 500:
# status = 'offline'
# elif code < 600:
# status = 'tempoffline'
# else:
# status = 'unknown'
# return status
