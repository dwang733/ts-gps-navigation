import time
from pathlib import Path

from filesystem import TsFileSystem

game_path = Path(
    R"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2"
)
mod_path = Path(R"C:\Users\dwang\Documents\Euro Truck Simulator 2\mod")


def parse_city_files():
    # file_path = def_path / "city.sii"
    # city_sii_file = SiiFile(file_path)
    # for city_path in city_sii_file.includes:
    #     print(city_path)
    #     sii_file = SiiFile(def_path / city_path)
    #     city = TsCity(sii_file)
    city_files = TsFileSystem.get_files("def", "city")
    for city_file in city_files:
        print(city_file.path)
        if city_file is None:
            raise FileNotFoundError(f"Could not find file 'def/{city_file}'")


def parse_def_files():
    """
    Parse all definition files.
    """

    parse_city_files()
    # TODO: parse_country_files()
    # TODO: parse_prefab_files()
    # TODO: parse_road_look_files()
    # TODO: parse_ferry_connections()


if __name__ == "__main__":
    try:
        start_time = time.time()
        TsFileSystem.mount_source_dir(game_path)
        # TsFileSystem.mount_source_dir(mod_path)
        end_time = time.time()
        print(end_time - start_time)

        parse_def_files()
    finally:
        TsFileSystem.close_file_buffers()
