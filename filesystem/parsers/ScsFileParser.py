import zlib
from dataclasses import dataclass
from struct import Struct
from typing import BinaryIO

from filesystem.TsDirectory import TsDirectory
from filesystem.TsFile import TsFile
from utils import StructDataClass


@dataclass
class _Header(StructDataClass):
    struct = Struct("<4sH2x4sII")

    magic: bytes  # 'SCS#'
    version: int  # u2
    # salt: int  # u2
    hash_method: bytes  # 'CITY'
    num_entries: int  # u4
    ofs_entries: int  # u4

    def __post_init__(self):
        assert self.magic == b"SCS#"
        assert self.version == 1
        assert self.hash_method == b"CITY"


@dataclass
class _Entry(StructDataClass):
    struct = Struct("<QQI4xII")

    hash: int  # u8
    ofs_body: int  # u8
    flags: int  # u4
    # crc: int  # u4
    len_body_uncompressed: int  # u4
    len_body_compressed: int  # u4


class ScsFileParser:
    """
    A static class used to parse .scs files.
    """

    @staticmethod
    def parse(f: BinaryIO) -> tuple[dict[int, TsDirectory], dict[int, TsFile]]:
        """
        Parse a .scs file to get its file structure.
        Args:
            f: The binary stream to parse.

        Returns:
            A tuple of 2 dictionaries.
            The 1st dictionary maps a hashed directory path (e.g. 'def/city') to a directory.
            The 2nd dictionary maps a hashed file path (e.g 'def/city.sii') to a file.
        """
        dirs: dict[int, TsDirectory] = {}
        files: dict[int, TsFile] = {}

        # Read header.
        f.seek(0)
        header = _Header.parse(f)

        # Read entries.
        f.seek(header.ofs_entries)
        for entry in _Entry.iter_parse(f, header.num_entries):
            # Parse each hash entry.
            is_directory = entry.flags & 1

            if is_directory:
                # Directory contents contain names of subdirectories and subfiles.
                # Each name is relative to parent directory, and has no leading or trailing slashes.
                # e.g. subdirectory name: country
                # e.g. subfile name: license_plates.sii
                dir = dirs.setdefault(entry.hash, TsDirectory())
                body = ScsFileParser._read_entry_body(f, entry)
                body_lines = body.decode(encoding="cp437").splitlines()

                for line in body_lines:
                    if not line:
                        continue

                    # Strip leading and trailing slashes for safety.
                    if line.startswith("*"):
                        dir.dir_names.add(line[1:].strip("/\\"))
                    else:
                        dir.file_names.add(line.strip("/\\"))
            else:
                files[entry.hash] = TsFile(
                    entry.hash,
                    lambda f=f, entry=entry: ScsFileParser._read_entry_body(f, entry),
                )

        return dirs, files

    @staticmethod
    def _read_entry_body(f: BinaryIO, entry: _Entry) -> bytes:
        old_pos = f.tell()
        try:
            f.seek(entry.ofs_body)
            data = f.read(entry.len_body_compressed)
            if entry.len_body_uncompressed > entry.len_body_compressed > 0:
                data = zlib.decompress(data)
            return data
        finally:
            f.seek(old_pos)
