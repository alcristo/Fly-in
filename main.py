from parser import Parser, ParsingError
from map import Map, Algorithm
from map_draw import draw_map


def parse_solution(solution: str, n: int) -> dict[int, list[str]]:
    drone_orders: dict[int, list[str]] = {}
    turn_orders = solution.splitlines()
    for i in range(n):
        drone_orders.update({i + 1: []})
    for turn in turn_orders:
        orders = turn.split(": ")[1].split()
        current: dict[int, str] = {}
        for order in orders:
            do = order.split('-')
            i = int(do[0][1:])
            current.update({i: do[1]})
        for i in range(n):
            if not current.get(i + 1):
                drone_orders[i + 1].append("")
            else:
                drone_orders[i + 1].append(current[i + 1])
    return drone_orders


def main() -> None:
    parser = Parser()
    path = "./maps/challenger/01_the_impossible_dream.txt"
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
    # print("Parsing was successful")
    # print(data)
    map = Map()
    map.fill_map(data)
    algo = Algorithm(map)
    solution = algo.solve()
    print()
    print(solution)
    parsed_sol = parse_solution(solution, map.drones)
    print()
    for i, orders in parsed_sol.items():
        print(f"{i}: {' '.join(orders)}")
    draw_map(map, parsed_sol, 100)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
