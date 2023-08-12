# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
import zlib


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class TsScs(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.header = TsScs.Header(self._io, self, self._root)

    class Header(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x53\x43\x53\x23":
                raise kaitaistruct.ValidationNotEqualError(b"\x53\x43\x53\x23", self.magic, self._io, u"/types/header/seq/0")
            self.version = self._io.read_bytes(2)
            if not self.version == b"\x01\x00":
                raise kaitaistruct.ValidationNotEqualError(b"\x01\x00", self.version, self._io, u"/types/header/seq/1")
            self.salt = self._io.read_u2le()
            self.hash_method = self._io.read_bytes(4)
            if not self.hash_method == b"\x43\x49\x54\x59":
                raise kaitaistruct.ValidationNotEqualError(b"\x43\x49\x54\x59", self.hash_method, self._io, u"/types/header/seq/3")
            self.num_entries = self._io.read_u4le()
            self.ofs_entries = self._io.read_u4le()


    class Entry(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.hash = self._io.read_u8le()
            self.ofs_body = self._io.read_u8le()
            self.is_directory = self._io.read_bits_int_le(1) != 0
            self.is_compressed = self._io.read_bits_int_le(1) != 0
            self.reserved = self._io.read_bits_int_le(30)
            self._io.align_to_byte()
            self.crc = self._io.read_u4le()
            self.len_body = self._io.read_u4le()
            self.len_data = self._io.read_u4le()

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data

            io = self._root._io
            _pos = io.pos()
            io.seek(self.ofs_body)
            self._m_data = io.read_bytes(self.len_data)
            io.seek(_pos)
            return getattr(self, '_m_data', None)

        @property
        def body(self):
            if hasattr(self, '_m_body'):
                return self._m_body

            if  ((self.is_compressed == True) and (self.len_data != 0)) :
                io = self._root._io
                _pos = io.pos()
                io.seek(self.ofs_body)
                self._raw__m_body = io.read_bytes(self.len_data)
                self._m_body = zlib.decompress(self._raw__m_body)
                io.seek(_pos)

            return getattr(self, '_m_body', None)


    @property
    def entries(self):
        if hasattr(self, '_m_entries'):
            return self._m_entries

        _pos = self._io.pos()
        self._io.seek(self.header.ofs_entries)
        self._m_entries = []
        for i in range(self.header.num_entries):
            self._m_entries.append(TsScs.Entry(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_entries', None)


