meta:
  id: ts_scs
  file-extension: scs
  bit-endian: le
  endian: le
seq:
  - id: header
    type: header
instances:
  entries:
    pos: header.ofs_entries
    type: entry
    repeat: expr
    repeat-expr: header.num_entries
types:
  header:
    seq:
      - id: magic
        contents: SCS#
      - id: version
        contents: [1, 0]
      - id: salt
        type: u2
      - id: hash_method
        contents: CITY
      - id: num_entries
        type: u4
      - id: ofs_entries
        type: u4
  entry:
    seq:
      - id: hash
        type: u8
      - id: ofs_body
        type: u8
      - id: is_directory
        type: b1
      - id: is_compressed
        type: b1
      - id: reserved
        type: b30
      - id: crc
        type: u4
      - id: len_body
        type: u4
      - id: len_data
        type: u4
    instances:
      data:
        io: _root._io
        pos: ofs_body
        size: len_data
      body:
        io: _root._io
        pos: ofs_body
        size: len_data
        process: zlib
        if: is_compressed == true and len_data != 0
