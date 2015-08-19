# -*- coding: utf-8 -*-

import re
import random
import pycurl

from module.common.json_layer import json_loads, json_dumps
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getRequest as get_request
from module.plugins.internal.Addon import Addon

class TransmissionRPC(Addon):
    __name__ = "TransmissionRPC"
    __type__ = "hook"
    __status__  = "testing"

    __pattern__ = r"https?://.+\.torrent|magnet:\?.+"
    __config__  = [("transmissionrpcurl" , "string" , "Transmission RPC URL" , "http://127.0.0.1:9091/transmission/rpc")]

    __version__ = "0.1"
    __description__ = """Send torrent and magnet URLs to Transmission Bittorent daemon via RPC"""
    __authors__ = [("GammaC0de", None)]


    def init(self):
        self.event_map = {'linksAdded': "links_added"}


    def links_added(self, links, pid):
        for link in links:
            m = re.search(self.__pattern__, link)
            if m:
                self.log_debug("sending link: %s" % link)
                self.SendToTransmission(link)
                links.remove(link)


    def SendToTransmission(self, url):
        transmission_rpc_url = self.get_config('transmissionrpcurl')
        client_request_id = self.__name__ + "".join(random.choice('0123456789ABCDEF') for _i in xrange(4))
        req = get_request()

        try:
            response = self.load(transmission_rpc_url,
                                 post=json_dumps({'arguments': {'filename': url},
                                                  'method'   : 'torrent-add',
                                                  'tag'      : client_request_id}),
                                 req=req)

        except BadHeader, e:
            if e.code == 409:
                headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", req.header))
                session_id = headers['X-Transmission-Session-Id']
                req.c.setopt(pycurl.HTTPHEADER, ["X-Transmission-Session-Id: %s" % session_id])
                response = self.load(transmission_rpc_url,
                                     post=json_dumps({'arguments': {'filename': url},
                                                      'method'   : 'torrent-add',
                                                      'tag'      : client_request_id}),
                                     req=req)

            else:
                 self.log_error(e)

        except Exception, e:
             self.log_error(e)

        try:
            res = json_loads(response)
            if "result" in res:
                self.log_debug("result: %s" % res['result'])

        except Exception, e:
            self.log_error(e)
