from pathlib import Path
from typing import BinaryIO

# SCS uses an old version of CityHash,
# so we need to use this instead of the cityhash pip package.
# VSCode also doesn't recognize it as a module, so need to use cast.
from clickhouse_cityhash.cityhash import CityHash64

from .TsDirectory import TsDirectory
from .TsFile import TsFile
from .parsers.ScsFileParser import ScsFileParser
from .parsers.ZipFileParser import ZipFileParser


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
            dir_path: The absolute directory path, with a leading slash.
            file_filter: Optional substring that the file name must contain.

        Returns:
            A list of files, or None if not found.
        """
        # Ensure consistent path (w/ leading and trailing slashes).
        if not dir_path.startswith("/"):
            raise ValueError(f"Directory path '{dir_path}' must be absolute.")
        if not dir_path.endswith("/"):
            dir_path += "/"

        # Hash is calculated without leading or trailing slashes.
        dir_hash: int = CityHash64(dir_path.strip("/\\"))
        dir = cls._dirs.get(dir_hash)

        files = []
        for file_name in dir.file_names:
            if file_filter in file_name:
                file_path = f"{dir_path}{file_name}" if dir_path else f"/{file_name}"
                file = cls.get_file(file_path)
                files.append(file)

                # File names are hashed, so we didn't know the name beforehand.
                file.path = file_path
        return files

    @classmethod
    def get_file(cls, file_path: str) -> TsFile | None:
        """
        Get a file in the file system.

        Args:
            file_path: The absolute file path, with a leading slash.

        Returns:
            A file, or None if not found.
        """
        # Ensure consistent path (w/ leading slash).
        if not file_path.startswith("/"):
            raise ValueError(f"File path '{file_path}' must be absolute.")

        # Hash is calculated without leading or trailing slashes.
        file_hash: int = CityHash64(file_path.strip("/\\"))
        file = cls._files.get(file_hash)

        # File names are hashed, so we didn't know the name beforehand.
        file.path = file_path
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
            raise FileNotFoundError(f"Could not find source directory '{path}'.")

        # Parse each .scs file.
        scs_files = path.glob("*.scs")
        for file in scs_files:
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
            raise FileNotFoundError(f"Could not find source file '{path}'.")

        # if "def" not in path.name:
        #     return

        f = path.open(mode="rb")
        try:
            dirs, files = ScsFileParser.parse(f)
            print(f"Parsed {path} as .scs file")
        except AssertionError:
            dirs, files = ZipFileParser.parse(f)
            print(f"Parsed {path} as .zip file")

        for dir_hash, dir in dirs.items():
            existing_dir = cls._dirs.get(dir_hash)
            if existing_dir:
                existing_dir.dir_names.update(dir.dir_names)
                existing_dir.file_names.update(dir.file_names)
            else:
                cls._dirs[dir_hash] = dir

        # Overwrite if there is already a file with the same hash.
        for file_hash, file in files.items():
            cls._files[file_hash] = file

    @classmethod
    def close_file_buffers(cls) -> None:
        """
        Close any open file buffers from mounting source files.
        """
        for f in cls._file_buffers:
            f.close()
