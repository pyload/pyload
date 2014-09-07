# -*- coding: utf-8 -*-

from thriftgen.pyload import Pyload

class Processor(Pyload.Processor):
    def __init__(self, *args, **kwargs):
        Pyload.Processor.__init__(self, *args, **kwargs)
        self.authenticated = {}

    def process(self, iprot, oprot):
        trans = oprot.trans
        if trans not in self.authenticated:
            self.authenticated[trans] = False
            oldclose = trans.close

            def wrap():
                if self in self.authenticated:
                    del self.authenticated[trans]
                oldclose()

            trans.close = wrap
        authenticated = self.authenticated[trans]
        (name, type, seqid) = iprot.readMessageBegin()

        # unknown method
        if name not in self._processMap:
            iprot.skip(Pyload.TType.STRUCT)
            iprot.readMessageEnd()
            x = Pyload.TApplicationException(Pyload.TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, Pyload.TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return

        # not logged in
        elif not authenticated and not name == "login":
            iprot.skip(Pyload.TType.STRUCT)
            iprot.readMessageEnd()
            # 20 - Not logged in (in situ declared error code)
            x = Pyload.TApplicationException(20, 'Not logged in')
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
            # api login
            self.authenticated[trans] = self._handler.checkAuth(args.username, args.password, trans.remoteaddr[0])

            result.success = True if self.authenticated[trans] else False
            oprot.writeMessageBegin("login", Pyload.TMessageType.REPLY, seqid)
            result.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()

        elif self._handler.isAuthorized(name, authenticated):
            self._processMap[name](self, seqid, iprot, oprot)

        else:
            #no permission
            iprot.skip(Pyload.TType.STRUCT)
            iprot.readMessageEnd()
            # 21 - Not authorized
            x = Pyload.TApplicationException(21, 'Not authorized')
            oprot.writeMessageBegin(name, Pyload.TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return

        return True
