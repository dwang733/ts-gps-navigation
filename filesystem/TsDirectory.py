from structs import TsScs


class TsDirectory:
    def __init__(self, entry: TsScs.Entry):
        self._entry = entry
        self._sub_dir_names: list[str] = []
        self._sub_file_names: list[str] = []

    @property
    def dir_names(self):
        return self._sub_dir_names

    @property
    def file_names(self):
        return self._sub_file_names
