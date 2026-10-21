from exceptions import ParsingError, MapError
from parser import Parser
from map import Map, Algorithm
from map_draw import draw_map
import sys
import pygame
import screeninfo  # noqa


def parse_solution(solution: str, n: int) -> dict[int, list[str]]:
    """
    Parse the solution

    Arguments:
        solution: the MAPF solution.
        n:  the number of drones.

    Returns:
        drone_orders: a time-ordered dictionary with list of moves as values.
    """
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


def menu() -> str:
    """If no arguments map provided, go to this menu, return map file path"""
    print("\x1b[H\x1b[0J", end="")
    print(rainbow_text("Fly-in"))
    print()
    print(
        "A Multi-Agent Pathfinding program in graphs.\n"
        "Author: alcristo\n"
        "Pathfinding algorithm: A* with prioritized planning\n"
    )
    print("DEFAULT MAPS\n")
    print("\x1b[92mEasy maps\x1b[0m")
    print("1: \x1b[92mLinear Path\x1b[0m")
    print("2: \x1b[92mSimple Fork\x1b[0m")
    print("3: \x1b[92mBasic Capacity\x1b[0m")
    print()
    print("\x1b[93mMedium maps\x1b[0m")
    print("4: \x1b[93mDead End Trap\x1b[0m")
    print("5: \x1b[93mCircular Loop\x1b[0m")
    print("6: \x1b[93mPriority Puzzle\x1b[0m")
    print()
    print("\x1b[91mHard maps\x1b[0m")
    print("7: \x1b[91mMaze Nightmare\x1b[0m")
    print("8: \x1b[91mCapacity Hell\x1b[0m")
    print("9: \x1b[91mUltimate Challenge\x1b[0m")
    print()
    print("\x1b[38;2;150;90;200mChallenge map\x1b[0m")
    print("10: \x1b[38;2;150;90;200mTHE IMPOSSIBLE DREAM\x1b[0m")
    print()
    level = input("Enter the level number or the map file route: ")
    if level == "1":
        path = "maps/easy/01_linear_path.txt"
    elif level == "2":
        path = "maps/easy/02_simple_fork.txt"
    elif level == "3":
        path = "maps/easy/03_basic_capacity.txt"
    elif level == "4":
        path = "maps/medium/01_dead_end_trap.txt"
    elif level == "5":
        path = "maps/medium/02_circular_loop.txt"
    elif level == "6":
        path = "maps/medium/03_priority_puzzle.txt"
    elif level == "7":
        path = "maps/hard/01_maze_nightmare.txt"
    elif level == "8":
        path = "maps/hard/02_capacity_hell.txt"
    elif level == "9":
        path = "maps/hard/03_ultimate_challenge.txt"
    elif level == "10":
        path = "maps/challenger/01_the_impossible_dream.txt"
    elif not level:
        raise EOFError
    else:
        path = level
    return path


def rainbow_text(text: str) -> str:
    """Return same string with rotated colors in the characters"""
    rainbow_str: list[str] = []
    reset = "\x1b[0m"
    rainbow_list = [
        "\x1b[91m",
        "\x1b[93m",
        "\x1b[92m",
        "\x1b[96m",
        "\x1b[94m",
        "\x1b[95m",
    ]
    i = 0
    for c in text:
        rainbow_str.append(f"{rainbow_list[i]}{c}{reset}")
        if not c.isspace():
            i = (i + 1) % len(rainbow_list)
    return "".join(rainbow_str)


def color_hub(name: str, map: Map) -> str:
    """
    Format a hub ID with its color.

    Arguments:
        name: the hub ID.
        map: the graph map.

    Returns:
        color_text: the colored hub name
             (defaults to white if color not in Pygame `ColorDict`)
    """
    reset = "\x1b[0m"
    color_name = map.hub(name).color
    try:
        color = pygame.Color(color_name)
    except pygame.error:
        if color_name == "rainbow":
            return rainbow_text(name)
        else:
            color = pygame.Color("white")
    rgb = (color.r, color.g, color.b)
    ansi = f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
    color_text = f"{ansi}{name}{reset}"
    return color_text


def print_solution(solution: str, map: Map) -> None:
    """
    Print solution with colors.

    Arguments:
        solution: the solution to `map`.
        map: the MAPF problem, for colors.
    """
    lines = solution.splitlines()
    for line in lines:
        turn = line.split(': ')[1].split(' ')
        colorline: list[str] = []
        for inst in turn:
            order = inst.split('-')
            if '→' in order[1]:
                ids = order[1].split('→')
                colorline.append(
                    f"{order[0]}-"
                    f"{color_hub(ids[0], map)}→{color_hub(ids[1], map)}"
                )
            else:
                colorline.append(f"{order[0]}-{color_hub(order[1], map)}")
        print(' '.join(colorline))


def main() -> None:
    """Run the program"""
    args = sys.argv.copy()
    args.pop(0)
    if not args:
        path = menu()
    else:
        if len(args) == 1:
            path = args[0]
        else:
            print("Error: multiple arguments")
            return
    monitor = screeninfo.get_monitors()[0]
    screen_size = (monitor.width, monitor.height)
    resolution: tuple[int, int] = (screen_size[0] // 2, screen_size[1] // 2)
    parser = Parser()
    try:
        data = parser.parse(path)
    except ParsingError as e:
        print(f"Caught ParsingError: {e.__str__()}")
        return
    except ValueError as e:
        print(f"Caught ValueError: {e.__str__()}")
        return
    except Exception as e:
        print(f"Caught Exception: {e.__str__()}")
        return
    map = Map()
    map.fill_map(data)
    map.init_h()
    algo = Algorithm(map)
    solution = algo.solve()
    print()
    print_solution(solution, map)
    parsed_sol = parse_solution(solution, map.drones)
    draw_map(map, parsed_sol, 100, resolution)


if __name__ == "__main__":
    try:
        main()
    except MapError as e:
        print(e.__str__())
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    except BaseException as e:
        print(e)
