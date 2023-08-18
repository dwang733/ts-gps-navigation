from dataclasses import dataclass
from struct import Struct
from typing import BinaryIO, ClassVar, Iterator, Self


@dataclass
class StructDataClass:
    """
    A dataclass that is parsed from a struct.
    """

    struct: ClassVar[Struct]
    """The struct used to unpack bytes into this data class."""

    @classmethod
    def parse(cls, buffer: bytes | BinaryIO) -> Self:
        """
        Parse this dataclass from a buffer.
        If a BinaryIO is passed in, the cursor is not moved back after reading.

        Args:
            buffer: The bytes or binary stream to parse.

        Returns:
            An instance of the dataclass.
        """
        b: bytes
        if isinstance(buffer, bytes):
            b = buffer
        else:
            b = buffer.read(cls.struct.size)
        return cls(*cls.struct.unpack(b))

    @classmethod
    def iter_parse(cls, buffer: bytes | BinaryIO, num_entries: int) -> Iterator[Self]:
        """
        Parse an iterable of this dataclass from a buffer.
        If a BinaryIO is passed in, the cursor is not moved back after reading.

        Args:
            buffer: The binary stream or bytes to parse.
            num_entries: The number of entries to parse.

        Returns:
            An iterable of the dataclass.
        """
        # Read all entries at once for speed.
        b: bytes
        if isinstance(buffer, bytes):
            b = buffer
        else:
            b = buffer.read(cls.struct.size * num_entries)
        return (cls(*t) for t in cls.struct.iter_unpack(b))
