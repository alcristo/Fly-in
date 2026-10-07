from parser import Parser, ParsingError


def main() -> None:
    parser = Parser()
    path = "./maps/not_valid/13_duplicated_connection.txt"
    # parser.parse(path)
    try:
        parser.parse(path)
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


if __name__ == "__main__":
    main()
