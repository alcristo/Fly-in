*This project has been created as part of the 42 curriculum by [alcristo](https://github.com/alcristo)*

# [Fly-in](https://github.com/alcristo/Fly-in)

## Description

Fly-in is a multi-agent pathfinding (MAPF) Python project in which a certain number of drones (agents) must traverse a graph from a starting vertex (here referenced as node, hub or zone) to a goal hub by traversing the graph edges (here referred as links or connections), while respecting capacity restrictions and hub zone types. This project includes visual representation in terminal and in graphic window via `Pygame`.

### Graph characteristics

A level consists of a graph with the following elements:

| Element | Description
| -------- | ------------- |
| `nb_drones` | The number of drones in the map |
| `start_hub` | The graph vertex where all drones start |
| `end_hub` | The graph vertex where all drones must travel to |
| `hub` | Any other vertex in the graph |
| `connection` | An edge in the graph |

Hubs in the map have a name for identification and a logical position made by two integers. Hubs have also the following properties as metadata:

* `color`: the hub color, represented by any string.
* `zone`: the zone type, which will make drones act differently.
* `max_drones`: the maximum number of drones that the hub can hold at a time.

Hub zone types can be:

| Zone | Description |
| ---- | -------------- |
| `normal` | Drones take a turn to get to the hub and another one to leave it. |
| `restricted` | Drones take two turns to get to the hub, but only one to leave it. |
| `priority` | A normal hub that will have priority during pathfinding. |
| `blocked` | Drones can't get there. Counts as if it doesn't exist. |

On the other hand, connections don't have identifiers, but only the hubs they connect. It has also the following metadata:

* `max_link_capacity`: the maximum number of drones that must traverse the connection at a time. Drones traversing to restricted hubs are considered to stay in the connection during two turns.

A valid map is considered to have only a start hub and an end hub, a positive number of drones and capacities for all nodes and links, and all hubs having valid zone types. Colors that don't appear in the Pygame `ColorDict` will be set to white. Disconnected maps will be rejected as the A* search will deem them unsolvable. Start hub is forced to set as normal. Both hubs and connections are validated by `Pydantic`.

### Algorithm: A* Prioritized Planning Search

When the map has been completed, the pathfinding algorithm will search for a solution for the problem. I used an A* search with prioritized planning. Prioritized planning divides a $n$-agent MAPF problem into $n$ single agent pathfinding problems. First, starting from the goal hub, all hubs are assigned a heuristic, which is its distance from the goal hub; another unit is added if restricted and infinity if blocked. If the start hub has an infinite heuristic, then the map has no solution. Then, all agents are labelled with numbers from 1 to $n$, and A* search is used to calculate the optimal route for the first agent, which will have no other obstacles than the map itself; and the solution is saved as a space-time list of reservations. Next, A* search is used on the second drone, which will have to plan its route according to the reservations of the first drone; saving its solution as another space-time list of reservations. Finally, this step is repeated for all the next drones, planning their movements according to the previous drones movements.

A* search is a widely used pathfinding algorithm. It is based on the optimization of $f = g + h$, where $g$ is the distance from the start vertex and $h$ is the ideal distance to the goal vertex. Here, time is a variable to keep track of, so $g$ will be the total number of turns. First, the initial state (number of turns, hub) is saved in an "open set", which will be a min $f$ heap implemented with the `heapq` default module. Then the state is moved to a closed set and all next neighbour states are moved into the heap. For each node, $f$ is calculated, but priority zones will be substracted $0.1$. Nodes containing the start hub and blocked zones are discarded. This process continues until the goal hub is reached, and then the reservations are saved for future path search.

### Visual Representation

The visual representation of the solution uses both terminal and Pygame.

In terminal, the solution is printed with the following format:

```
D1-{hub1_1} D2-{hub2_1} ...
D1-{hub1_2} D2-{hub2_2} ...
D1-{hub1_2}→{hub1_3} D2-{hub2_2} ...
...
```

The hub names are represented with their color string according to the Pygame `ColorDict`. If it doesn't exist then it's set to white, except `rainbow`, where the characters rotate colors.

In addition to the terminal, a Pygame window is opened representing the graph with the drone routes. At startup the animation is paused and the drones are at the start hub. The user can pan and zoom the camera for enhanced user experience. To start the animation press the play button. To reset the animation press the replay button, and the pause will then be active even if the animation was in play mode. Fast forward and slow down buttons were also implemented, as well as a turn counter to see the turns while the drones are moving.

This window occupies a quarter of the monitor, whose size is get via the `screeninfo` PyPI module.

## Instructions

First create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The project contains a Makefile with the following rules:

| Rule | Description |
| ---- | -------------- |
| install | Install the dependencies |
| run | Run the project |
| debug | Debug the project with PDB |
| clean | Remove temporal cache |
| lint | Execute flake8 and mypy |
| lint-strict | Execute flake8 and mypy --strict |

To execute any of the rules run:

```bash
make <rule>
```

When the project is run, a menu will appear. The user will then enter a number from 1 to 10 to select a default pathfinding map. The user can also make their own map and enter the route to the map file.

### Default maps

There are ten maps in total:

| Map | Difficulty | Drones | Reference turns | Score | Description |
| --- | ---------- | ------ | --------------- | ----- | ----------- |
| Linear Path | Easy | 2 | 6 | 4 | Simple linear path |
| Simple Fork | Easy | 4 | 8 | 4 | Simple fork with two paths |
| Basic Capacity | Easy | 4 | 6 | 4 | Basic capacity management |
| Dead End Trap | Medium | 5 | 12 | 8 | Dead end trap - drones might get stuck |
| Circular Loop | Medium | 6 | 15 | 15 | Circular loop with restricted zones |
| Priority Puzzle | Medium | 5 | 12 | 7 | Priority zones create optimal path challenges |
| Maze Nightmare | Hard | 8 | 30 | 13 | Complex maze with multiple dead ends and loops |
| Capacity Hell | Hard | 12 | 35 | 16 | Extreme capacity constraints with timing challenges |
| Ultimate Challenge | Hard | 15 | 45 | 26 | THE ULTIMATE CHALLENGE - All tricks combined |
| The Impossible Dream | Challenge | 25 | 45 | 43 | Extremely challenging map, may not be solvable by most algorithms |

### Custom maps

To create a custom map, a text file will suffice. However, it must have the following format:

```
# Comments (with hash marks as first character) are ignored at parsing, as well as empty lines
# n > 0; must be first line
nb_drones: n
# M > 0; x: int, y: int; only 1 start_hub
start_hub: start_name x y [color=any zone=any max_drones=M]
hub: hub1 x y [metadata=any ...]
hub: hub2 x y [metadata=any ...]
...
# M > 0; x: int, y: int; only 1 end_hub
end_hub: end_name x y [metadata=any ...]
connection: start_name-hub1 [max_link_capacity=M]
connection: hub1-hub2 [metadata=any]
...
```

It is recommended to put the connections at the end of the file; otherwise exceptions may arise. Invalid values for valid metadata types will raise exceptions. Invalid metadata types will be ignored.

## Resources

[Wikipedia page for Multi-agent pathfinding](https://en.wikipedia.org/wiki/Multi-agent_pathfinding) for documentation on this specific project.

[Pygame official documentation](https://www.pygame.org/docs/).

My [A-Maze-ing](https://github.com/alcristo/A-Maze-ing) project, from where my pathfinding algorithm is based on.

[Pixilart](https://www.pixilart.com/draw), where I drew the drone sprite.

The [screeninfo module](https://pypi.org/project/screeninfo/).

42 for the default maps.

### AI Usage

Artificial inteligence was used to create the initial architechture and debugging.