from parser import Parser, ParsingError
from map import Map
from pygame_test import draw_map


def main() -> None:
    parser = Parser()
    path = "./maps/easy/01_linear_path.txt"
    # parser.parse(path)
    try:
        data = parser.parse(path)
    except ParsingError as e:
        print(f"Caught ParsingError: {e.__str__()}")
        return
    except ValueError as e:
        print(f"Caught ValueError: {e.__str__()}")
        return
    except Exception as e:
        print(f"Caught Exception: {e}")
        return
    print("Parsing was successful")
    map = Map()
    map.fill_map(data)
    draw_map(map, 100)


if __name__ == "__main__":
    main()
