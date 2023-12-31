import time
from pathlib import Path

from filesystem import TsFileSystem
from sectors import TsSector
from units import TsCity

game_path = Path(
    R"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2"
)
mod_path = Path(R"C:\Users\dwang\Documents\Euro Truck Simulator 2\mod")


cities: list[TsCity] = []


def parse_city_files():
    city_files = TsFileSystem.get_files("/def/", "city")
    if not city_files:
        raise FileNotFoundError(
            "Could not find files in directory '/def/' that contain 'city'."
        )

    for city_file in city_files:
        # TODO: Try to determine encoding
        try:
            lines = [
                line.strip() for line in city_file.read().decode("utf-8").splitlines()
            ]
        except:
            lines = [
                line.strip() for line in city_file.read().decode("cp437").splitlines()
            ]
        for line in lines:
            if not line.startswith("@include"):
                continue

            # Path could be absolute or relative to def/.
            include_file_path = line.split(" ")[1].strip('"')
            if not include_file_path.startswith("/"):
                include_file_path = f"/def/{include_file_path}"

            city = TsCity(include_file_path)
            cities.append(city)


def parse_def_files():
    """
    Parse all definition files.
    """
    parse_city_files()
    # TODO: parse_country_files()
    # TODO: parse_prefab_files()
    # TODO: parse_road_look_files()
    # TODO: parse_ferry_connections()


def parse_sector_files():
    # TODO: Read /map folder to get .mbd file to determine folder to read
    base_files = TsFileSystem.get_files("/map/europe", ".base")

    for base_file in base_files:
        # if "sec+0017+0010" not in base_file.path:
        #     continue

        print(f"Parsing .base file: {base_file.path}...")
        TsSector(base_file)


if __name__ == "__main__":
    try:
        start_time = time.time()
        TsFileSystem.mount_source_dir(game_path)
        # TsFileSystem.mount_source_dir(mod_path)
        end_time = time.time()
        print(f"Mounted source directories in {end_time - start_time:.2f}s.")

        # start_time = time.time()
        # parse_def_files()
        # end_time = time.time()
        # print(f"Parsed def files in {end_time - start_time:.2f}s.")

        start_time = time.time()
        parse_sector_files()
        end_time = time.time()
        print(f"Parsed sector files in {end_time - start_time:.2f}s.")
    finally:
        TsFileSystem.close_file_buffers()
