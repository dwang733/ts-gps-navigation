from pathlib import Path
from typing import BinaryIO, cast

# SCS uses an old version of CityHash,
# so we need to use this instead of the cityhash pip package.
# VSCode also doesn't recognize it as a module, so need to use cast.
from clickhouse_cityhash.cityhash import CityHash64
from kaitaistruct import ValidationNotEqualError

from structs import TsScs, Zip
from .TsDirectory import TsDirectory
from .TsFile import TsFile


class TsFileSystem:
    """
    The file system for ETS2/ATS.
    File structure is extracted from .scs files,
    either as custom SCS hash archives or ZIP archives.
    Files from the base game and mod are loaded in order.
    """

    _dirs: dict[int, TsDirectory] = {}
    _files: dict[int, TsFile] = {}
    _file_buffers: list[BinaryIO] = []

    @classmethod
    def get_files(cls, dir_path: str, file_filter: str = "") -> list[TsFile] | None:
        """
        Get files in the file system under the given directory  with an optional filter.

        Args:
            dir_path: The directory path.
            file_filter: Optional substring that the file must contain to be returned.

        Returns:
            A list of files, or None if not found.
        """
        dir_path = dir_path.strip("/")
        dir_hash: int = CityHash64(dir_path)
        dir = cls._dirs.get(dir_hash)

        files = []
        for file_name in dir.file_names:
            if file_filter in file_name:
                file_path = f"{dir_path}/{file_name}" if dir_path else file_name
                file = cls.get_file(file_path)
                files.append(file)

                # File names are hashed, we don't know the name beforehand.
                # Since we got the file path just now, let's fill in the file name.
                file.path = file_path
        return files

    @classmethod
    def get_file(cls, file_path: str) -> TsFile | None:
        """
        Get a file in the file system.

        Args:
            file_path: The file path.

        Returns:
            A file, or None if not found.
        """
        file_path = file_path.strip("/")
        file_hash: int = CityHash64(file_path)
        file = cls._files.get(file_hash)
        return file

    @classmethod
    def mount_source_dir(cls, path: Path) -> None:
        R"""
        Mount a directory which contains .scs files to be parsed.
        This should be the installation location of the game
        (e.g. C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2).

        Notes:
            Any file buffers opened are not closed here.
            You must call close_file_buffers() explicitly.

        Args:
            path: The path to the source directory.

        Returns:
            None

        Raises:
            FileNotFoundError: Source directory could not be found.
        """
        if not path.exists():
            raise FileNotFoundError(f"Could not find directory '{path}'")

        # Parse each .scs file.
        scs_files = path.glob("*.scs")
        for file in scs_files:
            # if file.name != "def.scs":
            #     continue
            cls.mount_source_file(file)

    @classmethod
    def mount_source_file(cls, path: Path) -> None:
        """
        Add the files and folders contained in the .scs file to the file system.
        An .scs file is an archive file (SCS hash archive or ZIP archive).

        Notes:
            Any file buffers opened are not closed here.
            You must call close_file_buffers() explicitly.

        Args:
            path: The path to the source file.

        Returns:
            None

        Raises:
            FileNotFoundError: Source file could not be found.
        """
        if not path.exists():
            raise FileNotFoundError(f"Could not find file '{path}'")

        # if "MaghrebMap_Model1_03.3_Beta" not in path.name:
        #     return

        # print(f"Mounting {path}")
        f = path.open(mode="rb")
        try:
            TsFileSystem._parse_scs_file(f)
        except ValidationNotEqualError:
            TsFileSystem._parse_zip_file(f)

    @classmethod
    def close_file_buffers(cls) -> None:
        """
        Close any open file buffers from mounting source files.
        """
        for f in cls._file_buffers:
            f.close()

    @classmethod
    def _parse_scs_file(cls, f: BinaryIO):
        f.seek(0)
        scs = TsScs.from_io(f)

        entries = cast(list[TsScs.Entry], scs.entries)
        for entry in entries:
            if entry.is_directory:
                # Create directory object if it does not exist.
                dir = cls._dirs.get(entry.hash)
                if dir is None:
                    dir = TsDirectory(entry)
                    cls._dirs[entry.hash] = dir

                # Use body, unless not compressed, then use original data.
                body = cast(bytes, entry.body or entry.data)
                body_lines = [i.decode(encoding="cp437") for i in body.splitlines()]

                for line in body_lines:
                    if line == "":
                        continue

                    if line.startswith("*"):
                        dir.dir_names.append(line[1:])
                    else:
                        dir.file_names.append(line)
            else:
                # Overwrite if there is already a file with the same hash
                # Force early binding of entry to closure.
                cls._files[entry.hash] = TsFile(
                    entry.hash, lambda e=entry: e.body or e.data
                )

    @classmethod
    def _parse_zip_file(cls, f: BinaryIO):
        f.seek(0)
        zip = Zip.from_io(f)
