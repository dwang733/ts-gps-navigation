import io
import zlib
from dataclasses import dataclass
from struct import Struct
from typing import BinaryIO

from clickhouse_cityhash.cityhash import CityHash64

from filesystem.TsDirectory import TsDirectory
from filesystem.TsFile import TsFile
from utils import StructDataClass


@dataclass
class _EndOfCentralDir(StructDataClass):
    struct = Struct("<2s2s6xHII2x")

    magic: str  # 'PK'
    section_type: bytes  # 0x05 0x06
    # disk_of_end_of_central_dir: int  # u2
    # disk_of_central_dir: int  # u2
    # num_central_dir_entries_on_disk: int  # u2
    num_central_dir_entries_total: int  # u2
    len_central_dir: int  # u4
    ofs_central_dir: int  # u4
    # len_comment: int  # u2
    # comment: bytes  # len_comment

    def __post_init__(self):
        assert self.magic == b"PK"
        assert self.section_type == b"\x05\x06"


@dataclass
class _CentralDirEntry(StructDataClass):
    struct = Struct("<2s2s16xIIHHH8xI")

    magic: str  # 'PK'
    section_type: bytes  # 0x01 0x02
    # version_made_by: int  # u2
    # version_needed_to_extract: int  # u2
    # flags: int  # u2
    # compression_method: int  # u2 (enum)
    # file_mod_time: int  # u4 (dos_datetime)
    # crc32: int  # u4
    len_body_compressed: int  # u4
    len_body_uncompressed: int  # u4
    len_file_name: int  # u2
    len_extra: int  # u2
    len_comment: int  # u2
    # disk_number_start: int  # u2
    # int_file_attr: int  # u2
    # ext_file_attr: int  # u4
    ofs_local_header: int  # u4
    # file_name: bytes  # len_file_name
    # extra: bytes  # len_extra (list of extra fields)
    # comment: bytes  # len_comment

    def __post_init__(self):
        assert self.magic == b"PK"
        assert self.section_type == b"\x01\x02"


@dataclass
class _LocalFileHeader(StructDataClass):
    struct = Struct("<2s2s22xHH")

    magic: str  # 'PK'
    section_type: bytes  # 0x03 0x04
    # version: int  # u2
    # flags: int  # u2
    # compression_method: int  # u2 (enum)
    # file_mod_time: int  # u4 (dos_datetime)
    # crc32: int  # u4
    # len_body_compressed: int  # u4
    # len_body_uncompressed: int  # u4
    len_file_name: int  # u2
    len_extra: int  # u2
    # file_name: bytes  # len_file_name
    # extra: bytes  # len_extra

    def __post_init__(self):
        assert self.magic == b"PK"
        assert self.section_type == b"\x03\x04"


class ZipFileParser:
    """
    A static class used to parse .zip files.
    """

    @staticmethod
    def parse(f: BinaryIO) -> tuple[dict[int, TsDirectory], dict[int, TsFile]]:
        """
        Parse a .zip file to get its file structure.
        Args:
            f: The binary stream to parse.

        Returns:
            A tuple of 2 dictionaries.
            The 1st dictionary maps a hashed directory path (e.g. 'def/city') to a directory.
            The 2nd dictionary maps a hashed file path (e.g 'def/city.sii') to a file.
        """
        dirs: dict[int, TsDirectory] = {}
        files: dict[int, TsFile] = {}

        # Read "End of Central Directory" (EOCD).
        # Assume len_comment is 0, so EOCD has fixed size.
        eocd_size = _EndOfCentralDir.struct.size
        f.seek(eocd_size * -1, io.SEEK_END)
        eocd_bytes = f.read(eocd_size)
        eocd = _EndOfCentralDir.parse(eocd_bytes)

        f.seek(eocd.ofs_central_dir)
        for i in range(eocd.num_central_dir_entries_total):
            # Read each central directory entry.
            entry = _CentralDirEntry.parse(f)

            # File path is absolute, and has no leading slashes but directories have a trailing slash.
            # e.g. directory name: def/country/
            # e.g. file name: def/country/germany/license_plates.sii
            # Note: zip files must use forward slashes, so we can ignore backwards slashes.
            file_path = f.read(entry.len_file_name).decode("cp437").strip("/")
            f.seek(entry.len_extra + entry.len_comment, io.SEEK_CUR)

            # Hash is calculated without leading or trailing slashes.
            file_hash: int = CityHash64(file_path)

            # Get the parent directory path and file/directory name from the file path.
            # Use normal split() instead of os.path or pathlib.Path due to better speed and known format.
            split_parts = file_path.rsplit("/", 1)
            if len(split_parts) == 2:
                parent_dir_path, file_tail = split_parts[0], split_parts[1]
            else:
                parent_dir_path = ""
                file_tail = split_parts[0]

            # Get the parent directory.
            parent_dir_hash: int = CityHash64(parent_dir_path)
            parent_dir = dirs.setdefault(parent_dir_hash, TsDirectory())

            is_directory = entry.len_body_compressed == 0
            if is_directory:
                parent_dir.dir_names.add(file_tail)
            else:
                # If entry is a file, get the body offset, which is after the local file header.
                prev_pos = f.tell()
                f.seek(entry.ofs_local_header)
                header = _LocalFileHeader.parse(f)
                ofs_body = (
                    entry.ofs_local_header
                    + _LocalFileHeader.struct.size
                    + header.len_file_name
                    + header.len_extra
                )
                f.seek(prev_pos)

                # Force early binding of entry to closure.
                files[file_hash] = TsFile(
                    file_hash,
                    lambda f=f, entry=entry, ofs_body=ofs_body: ZipFileParser._read_entry_body(
                        f, entry, ofs_body
                    ),
                )
                parent_dir.file_names.add(file_tail)

        return dirs, files

    @staticmethod
    def _read_entry_body(f: BinaryIO, entry: _CentralDirEntry, ofs_body: int) -> bytes:
        old_pos = f.tell()
        try:
            f.seek(ofs_body)
            data = f.read(entry.len_body_compressed)
            if (
                entry.len_body_uncompressed != entry.len_body_compressed
                and entry.len_body_compressed != 0
            ):
                # Set wbits since zip file uses 'deflate' format
                data = zlib.decompress(data, wbits=-zlib.MAX_WBITS)
            return data
        finally:
            f.seek(old_pos)
