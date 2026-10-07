from parser import Parser, ParsingError
import pydantic


def main() -> None:
    try:
        parser = Parser()
        path = "./maps/easy/02_simple_fork.txt"
        mapdata = parser.parse(path)
    except ParsingError as e:
        print(f"Caught ParsingError: {e.__str__()}")
        return
    except Exception as e:
        print(e)
        return
    print("Parsing was successful")


if __name__ == "__main__":
    print(f"Pydantic version: {pydantic.__version__}")
    main()
