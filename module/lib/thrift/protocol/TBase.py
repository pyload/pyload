#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#

from thrift.Thrift import *
from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport

try:
  from thrift.protocol import fastbinary
except:
  fastbinary = None

class TBase(object):
  __slots__ = []

  def __repr__(self):
    L = ['%s=%r' % (key, getattr(self, key))
              for key in self.__slots__ ]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    for attr in self.__slots__:
      my_val = getattr(self, attr)
      other_val = getattr(other, attr)
      if my_val != other_val:
        return False
    return True
    
  def __ne__(self, other):
    return not (self == other)
  
  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStruct(self, self.thrift_spec)

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStruct(self, self.thrift_spec)

class TExceptionBase(Exception):
  # old style class so python2.4 can raise exceptions derived from this
  #  This can't inherit from TBase because of that limitation.
  __slots__ = []
  
  __repr__ = TBase.__repr__.im_func
  __eq__ = TBase.__eq__.im_func
  __ne__ = TBase.__ne__.im_func
  read = TBase.read.im_func
  write = TBase.write.im_func

#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#

from thrift.Thrift import *
from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport

try:
  from thrift.protocol import fastbinary
except:
  fastbinary = None

def read(iprot, types, ftype, spec):
    try:
        return types[ftype][0]()
    except KeyError:
        if ftype == TType.LIST:
            ltype, lsize = iprot.readListBegin()

            value = [read(iprot, types, spec[0], spec[1]) for i in range(lsize)]

            iprot.readListEnd()
            return value
        
        elif ftype == TType.SET:
            ltype, lsize = iprot.readSetBegin()

            value = set([read(iprot, types, spec[0], spec[1]) for i in range(lsize)])

            iprot.readSetEnd()
            return value

        elif ftype == TType.MAP:
            key_type, key_spec = spec[0], spec[1]
            val_type, val_spec = spec[2], spec[3]

            ktype, vtype, mlen = iprot.readMapBegin()
            res = dict()

            for i in xrange(mlen):
                key = read(iprot, types, key_type, key_spec)
                res[key] = read(iprot, types, val_type, val_spec)

            iprot.readMapEnd()
            return res

        elif ftype == TType.STRUCT:
            return spec[0]().read(iprot)




def write(oprot, types, ftype, spec, value):
    try:
        types[ftype][1](value)
    except KeyError:
        if ftype == TType.LIST:
            oprot.writeListBegin(spec[0], len(value))

            for elem in value:
                write(oprot, types, spec[0], spec[1], elem)

            oprot.writeListEnd()
        elif ftype == TType.SET:
            oprot.writeSetBegin(spec[0], len(value))

            for elem in value:
                write(oprot, types, spec[0], spec[1], elem)
                
            oprot.writeSetEnd()
        elif ftype == TType.MAP:
            key_type, key_spec = spec[0], spec[1]
            val_type, val_spec = spec[2], spec[3]

            oprot.writeMapBegin(key_type, val_type, len(value))
            for key, val in value.iteritems():
                write(oprot, types, key_type, key_spec, key)
                write(oprot, types, val_type, val_spec, val)

            oprot.writeMapEnd()
        elif ftype == TType.STRUCT:
            value.write(oprot)


class TBase2(object):
    __slots__ = ("thrift_spec")

    #subclasses provides this information
    thrift_spec = ()

    def __repr__(self):
        L = ['%s=%r' % (key, getattr(self, key))
              for key in self.__slots__ ]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        for attr in self.__slots__:
            my_val = getattr(self, attr)
            other_val = getattr(other, attr)
            if my_val != other_val:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def read(self, iprot):
        if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
            fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
            return

        #local copies for faster access
        thrift_spec = self.thrift_spec
        setter = self.__setattr__

        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break

            try:
                specs = thrift_spec[fid]
                if not specs or specs[1] != ftype:
                    iprot.skip(ftype)

                else:
                    pos, etype, ename, espec, unk = specs
                    value = read(iprot, iprot.primTypes, etype, espec)
                    setter(ename, value)
                    
            except IndexError:
                iprot.skip()

            iprot.readFieldEnd()

        iprot.readStructEnd()

    def write(self, oprot):
        if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
            oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
            return

        #local copies for faster access
        oprot.writeStructBegin(self.__class__.__name__)
        getter = self.__getattribute__

        for spec in self.thrift_spec:
            if spec is None: continue
            # element attributes
            pos, etype, ename, espec, unk = spec
            value = getter(ename)
            if value is None: continue

            oprot.writeFieldBegin(ename, etype, pos)
            write(oprot, oprot.primTypes, etype, espec, value)
            oprot.writeFieldEnd()

        oprot.writeFieldStop()
        oprot.writeStructEnd()

class TBase(object):
  __slots__ = ('thrift_spec',)

  #provides by subclasses
  thrift_spec = ()

  def __repr__(self):
    L = ['%s=%r' % (key, getattr(self, key))
              for key in self.__slots__ ]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    for attr in self.__slots__:
      my_val = getattr(self, attr)
      other_val = getattr(other, attr)
      if my_val != other_val:
        return False
    return True
    
  def __ne__(self, other):
    return not (self == other)
  
  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStruct(self, self.thrift_spec)

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStruct(self, self.thrift_spec)

class TExceptionBase(Exception):
  # old style class so python2.4 can raise exceptions derived from this
  #  This can't inherit from TBase because of that limitation.
  __slots__ = []
  
  __repr__ = TBase.__repr__.im_func
  __eq__ = TBase.__eq__.im_func
  __ne__ = TBase.__ne__.im_func
  read = TBase.read.im_func
  write = TBase.write.im_func

