class TsDirectory:
    def __init__(self):
        self._sub_dir_names: set[str] = set()
        self._sub_file_names: set[str] = set()

        self.underlying_paths: list[str] = []

    @property
    def dir_names(self):
        return self._sub_dir_names

    @property
    def file_names(self):
        return self._sub_file_names
