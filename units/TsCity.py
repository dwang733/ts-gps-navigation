from filesystem import TsFileSystem


class TsCity:
    def __init__(self, file_path: str):
        file = TsFileSystem.get_file(file_path)
        if not file:
            raise FileNotFoundError(f"Could not find city file '{file_path}'")

        self.unit_name = ""
        self.name = ""
        self.localized_name = ""
        self.country = ""
        self.map_x_offsets: list[float] = []
        self.map_y_offsets: list[float] = []

        lines = [line.strip() for line in file.read().decode("utf-8").splitlines()]
        for line in lines:
            if ":" not in line:
                continue

            split_parts = [i.strip(' "') for i in line.split(":")]
            key, value = split_parts[0], split_parts[1]
            value = value.split(" ")[0]
            if key == "city_data":
                self.unit_name = value
            elif key == "city_name":
                self.name = value
            elif key == "city_name_localized":
                self.localized_name = value
            elif key == "country":
                self.country = value
            elif key == "map_x_offsets[]":
                self.map_x_offsets.append(float(value))
            elif key == "map_y_offsets[]":
                self.map_y_offsets.append(float(value))
