# -*- coding: utf-8 -*-

from thriftgen.pyload import Pyload

class Processor(Pyload.Processor):
    def __init__(self, *args, **kwargs):
        Pyload.Processor.__init__(self, *args, **kwargs)
        self.authenticated = {}

    def process(self, iprot, oprot):
        trans = oprot.trans
        if not self.authenticated.has_key(trans):
            self.authenticated[trans] = False
            oldclose = trans.close
            def wrap():
                del self.authenticated[trans]
                oldclose()
            trans.close = wrap
        authenticated = self.authenticated[trans]
        (name, type, seqid) = iprot.readMessageBegin()
        if name not in self._processMap or (not authenticated and not name == "login"):
            iprot.skip(Pyload.TType.STRUCT)
            iprot.readMessageEnd()
            x = Pyload.TApplicationException(Pyload.TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, Pyload.TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        elif not authenticated and name == "login":
            args = Pyload.login_args()
            args.read(iprot)
            iprot.readMessageEnd()
            result = Pyload.login_result()
            self.authenticated[trans] = self._handler.login(args.username, args.password, trans.remoteaddr[0])
            result.success = self.authenticated[trans]
            oprot.writeMessageBegin("login", Pyload.TMessageType.REPLY, seqid)
            result.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True
