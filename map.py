from __future__ import annotations
from models import Hub, Connection, MapData
from exceptions import NodeError, EdgeError, MapError
from typing import Any
from math import inf
import heapq


class Map:
    """
    Map class for graph storage.

    Arguments:
        drones: the number of drones in the level.
        hubs: a vertex dictionary with the names as keys.
        connections: an edge list to store the links between vertices.
        start_hub: the vertex where all drones will start.
        end_hub: the vertex where all drones must go.
    """

    drones: int = 0
    hubs: dict[str, Hub] = {}
    connections: list[Connection] = []
    start_hub: Hub
    goal_hub: Hub

    def add_hub(self, new: Hub) -> None:
        """
        Add new hub to the map.

        Arguments:
            new: the new vertex to add to the graph.

        Raises:
            NodeError: if `new` is already in map.
            AttributeError: if position is already occupied.
        """

        ids = [hub.id for hub in self.hubs.values()]
        if new.id in ids:
            raise NodeError(f"hub {new.id} already in map")
        for name in ids:
            if self.hubs[name].position == new.position:
                raise AttributeError(
                    f"({new.position[0]},{new.position[1]}) "
                    f"already occupied by {name}"
                )
        self.hubs.update({new.id: new})

    def add_connection(self, new: Connection) -> None:
        """
        Add new connection to the map.

        Arguments:
            new: the new edge to add to the graph.

        Raises:
            EdgeError: if connection already in map.
            AttributeError: if any off the hubs linked by `new` not in map.
        """
        hubs = (new.hub1, new.hub2)
        map_conns = [(edge.hub1, edge.hub2) for edge in self.connections]
        if hubs in map_conns:
            raise EdgeError(f"connection {hubs[0]}-{hubs[1]} already in map")
        hub_ids = [hub.id for hub in self.hubs.values()]
        if new.hub1.id not in hub_ids:
            raise AttributeError(f"hub not in map: {new.hub1.id}")
        if new.hub2.id not in hub_ids:
            raise AttributeError(f"hub not in map: {new.hub2.id}")
        self.connections.append(new)

    def get_connection(self, fro: str, to: str) -> Connection:
        """
        Get a connection from two hub names.

        Arguments:
            fro: the first hub ID.
            to: the second hub ID.

        Returns:
            edge: the desired connection.

        Raises:
            AttributeError: if `fro` and `to` hubs are not connected.
        """
        for edge in self.connections:
            if edge.hub1.id == fro:
                if edge.hub2.id == to:
                    return edge
            if edge.hub2.id == fro:
                if edge.hub1.id == to:
                    return edge
        raise AttributeError(f"connection not in map: {fro}-{to}")

    def hub(self, name: str) -> Hub:
        """Return hub from ID"""
        return self.hubs[name]

    def neighbours(self, name: str) -> set[str]:
        """Return set of hub IDs from a hub ID."""
        self.hubs[name]
        neighs: set[str] = set()
        for edge in self.connections:
            if name == edge.hub1.id:
                neighs.add(edge.hub2.id)
            elif name == edge.hub2.id:
                neighs.add(edge.hub1.id)
        return neighs

    def fill_map(self, map_data: MapData) -> None:
        """Use `map_data` to fill the graph"""
        self.drones = map_data.nb_drones
        self.start_hub = map_data.start_hub
        self.add_hub(map_data.start_hub)
        hubs = map_data.hubs
        for hub in hubs.values():
            self.add_hub(hub)
        self.add_hub(map_data.end_hub)
        self.goal_hub = map_data.end_hub
        for edge in map_data.connections:
            self.add_connection(edge)
            edge.hub1.connections.append(edge.hub2.id)
            edge.hub2.connections.append(edge.hub1.id)

    def init_h(self) -> None:
        """Initiate the vertex heuristic values"""
        if self.goal_hub.zone == "blocked":
            raise MapError(
                "map has no reachable solution from "
                f"{self.start_hub.id} to {self.goal_hub.id} "
                "(goal is blocked)"
            )
        open_heap: list[tuple[float, str]] = []
        cl_set: set[str] = set()
        current: str = self.goal_hub.id
        heapq.heappush(open_heap, (0, current))
        while len(open_heap):
            dist, current = heapq.heappop(open_heap)
            cl_set.add(current)
            if dist < self.hubs[current].heuristic:
                self.hubs[current].heuristic = dist
            neighbours = self.neighbours(current)
            for hub in neighbours:
                if hub in cl_set:
                    continue
                zone = 1.
                if self.hub(hub).zone == "restricted":
                    zone = 2
                elif self.hub(hub).zone == "blocked":
                    zone = inf
                heapq.heappush(open_heap, (dist + 1 + zone, hub))
        # for h, hub in open_heap:
            # self.hub(hub).heuristic = h
        if self.start_hub.heuristic == inf:
            raise MapError(
                "map has no reachable solution from "
                f"{self.start_hub.id} to {self.goal_hub.id}"
            )


class Reservations:
    """
    Class for storing the occupied vertices and edges at each turn.

    Arguments:
        vertex_occupancy: A dictionary with time steps as keys and values are
         dictionaries with hub names as keys and their occupancy as values.
        edge_occupancy: A dictionary with time steps as keys and values are
         dictionaries with a tuple of two hub names as keys
         and their occupancy as values.
    """
    vertex_occupancy: dict[int, dict[str, int]] = {}
    edge_occupancy: dict[int, dict[tuple[str, str], int]] = {}


def undirected_edge(u: str, v: str) -> tuple[str, str]:
    """Return tuple of two strings for Reservation class"""
    return (min((u, v)), max((u, v)))


class Drone:
    """Drone class for storing the drone's movements"""
    def __init__(self, number: int) -> None:
        """
        Initialize a Drone class

        Arguments:
            id: the drone's ID.
        """
        self.id = number
        self.plan: list[str] = []


class PathNode:
    """Class for storing the drone's path steps"""
    def __init__(self, new: Hub, fro: Hub | None = None):
        """
        Initialize a new path step.

        Arguments:
            new: the arrival hub.
            from: if `new` is restricted, the departure hub.
        """
        self.hub = new
        self.fro: Hub | None = None
        if new.zone == "restricted":
            self.fro = fro
        self._g: int = int(1e6)
        self._h: float = new.heuristic
        self._f: float = 1e12
        self.next: PathNode | None = None

    def __lt__(self, other: PathNode) -> bool:
        """Method for `PathNode` comparison"""
        if self.g < other.g:
            return True
        return False

    def __le__(self, other: PathNode) -> bool:
        """Method for `PathNode` comparison"""
        if self.g <= other.g:
            return True
        return False

    def __gt__(self, other: PathNode) -> bool:
        """Method for `PathNode` comparison"""
        if self.g > other.g:
            return True
        return False

    def __ge__(self, other: PathNode) -> bool:
        """Method for `PathNode` comparison"""
        if self.g >= other.g:
            return True
        return False

    def previous_hub(self) -> Hub:
        """Return previous hub from current"""
        current = self.hub.id
        node = self.next
        while node:
            if node.hub.id != current:
                return node.hub
            node = node.next
        return self.hub

    def hub_in_path(self) -> bool:
        """Return whether current hub is in path"""
        if None in (self, self.next):
            return False
        name = self.hub.id
        node = self.next
        while node and node.hub.id == name:
            node = node.next
        while node:
            if node.hub.id == name:
                return True
            node = node.next
            if node is self.next:
                break
        return False

    @staticmethod
    def node_in_set(name: str, turn: int, set: set[tuple[str, int]]) -> bool:
        """Return whether a node with hub ID `name` is in `set` at `turn`"""
        for node, t in set:
            if node == name and t == turn:
                return True
        return False

    @staticmethod
    def node_in_heap(name: str, heap: list[Any]) -> bool:
        """Return whether a node with hub ID `name` is in `heap`"""
        for node in heap:
            if node[1].hub.id == name:
                return True
        return False

    @property
    def g(self) -> int:
        """G score for A* search"""
        return self._g

    @g.setter
    def g(self, n: int) -> None:
        self._g = n
        self._f = self._g + self._h

    @property
    def h(self) -> float:
        """H score for A* search"""
        return self._h

    @h.setter
    def h(self, n: float) -> None:
        self._h = n
        self._f = self._g + self._h

    @property
    def f(self) -> float:
        return self._f


class Algorithm:
    """Class for MAPF problem solving"""
    def __init__(self, level: Map):
        """
        Initiate an `Algorithm` class.

        Arguments:
            level: the problem to solve as a `Map` class.
        """
        self.map = level
        self.drones: list[Drone] = []
        for i in range(level.drones):
            self.drones.append(Drone(i + 1))
        self.plans: list[list[str]] = []
        self.reservations = Reservations()
        self.turns = 0
        self.delivered = 0

    def _can_move(self, u: str, v: str, t: int) -> bool:
        """Return whether a drone can move from `u` to `v` at turn `t`"""
        if not self.reservations.vertex_occupancy:
            return True
        if not self.reservations.edge_occupancy:
            return True
        if u == v:
            return False
        to = self.map.hub(v)
        if to == self.map.goal_hub:
            to_cap = self.map.drones
        else:
            to_cap = to.capacity
        edge = undirected_edge(u, v)
        edge_cap = self.map.get_connection(u, v).capacity
        edge_occ = self.reservations.edge_occupancy.get(t, {}).get(edge, 0)
        if edge_occ >= edge_cap:
            return False
        t_arr = t + 1 if to.zone == "restricted" else t
        to_occ = self.reservations.vertex_occupancy.get(t_arr, {}).get(v, 0)
        if to.zone == "restricted":
            for check_turn in (t, t + 1):
                to_occ = self.reservations.vertex_occupancy.get(
                    check_turn, {}
                ).get(v, 0)
                if to_occ >= to_cap:
                    return False
        else:
            if to_occ >= to_cap:
                return False
        return True

    def _heuristic(self, node: PathNode) -> None:
        """Assign H score to `node`"""
        occupancy = self.hub_occupation(node.hub.id, int(node.g))
        node.h = node.hub.heuristic + occupancy / node.hub.capacity
        if node.hub_in_path():
            node.h += 5
        zone = node.hub.zone
        if zone == "priority":
            node.h -= .1
        elif zone == "blocked":
            node.h += inf

    def _a_star(self, start: Hub) -> PathNode:
        """Solve a MAPF problem from `start`"""

        # init open heap and closed set
        opened: list[tuple[float, PathNode]] = []
        closed: set[tuple[str, int]] = set()
        current = PathNode(start)
        current.g = 0
        heapq.heappush(opened, (current.f, current))
        g_list: dict[tuple[str, int], float] = {}
        f_list: dict[tuple[str, int], float] = {}
        t = 0

        # while nodes in open heap
        while len(opened):
            current = heapq.heappop(opened)[1]
            t = int(current.g)
            closed.add((current.hub.id, t))

            # if current is goal, exit
            if current.hub.id == self.map.goal_hub.id:
                return current

            # check neighbours
            for neighbour in self.map.neighbours(current.hub.id):
                prev = current
                t1 = t + 1
                hub = self.map.hub(neighbour)
                if not g_list.get((neighbour, t1)):
                    g_list.update({(neighbour, t1): inf})
                if not f_list.get((neighbour, t1)):
                    f_list.update(
                        {(neighbour, t1): g_list[
                            (neighbour, t1)
                        ] + hub.heuristic}
                    )
                if hub.zone == "blocked":
                    continue
                if PathNode.node_in_set(hub.id, t1, closed):
                    continue

                # if drone can't move, check reservations
                if not self._can_move(prev.hub.id, hub.id, t1):
                    current_hub = prev.hub
                    cap = current_hub.capacity
                    occ = self.reservations.vertex_occupancy.get(
                        t1, {}
                    ).get(current_hub.id, 0)
                    # if hub currently occupied, wait
                    if occ < cap:
                        node = PathNode(prev.hub)
                        node.next = prev
                        node.g = t1
                        node.h = prev.h
                        heapq.heappush(opened, (node.f, node))
                    continue

                # if restricted neighbour, occupy link
                elif hub.zone == "restricted":
                    r_node = PathNode(hub, prev.hub)
                    r_node.next = prev
                    r_node.g = t1
                    node = PathNode(hub)
                    node.next = r_node
                    node.g = t1 + 1
                else:
                    node = PathNode(hub)
                    node.next = prev
                    node.g = t1
                if not g_list.get((hub.id, node.g)):
                    g_list.update({(hub.id, node.g): node.g})

                # compute heuristics
                if node.hub == self.map.start_hub:
                    continue
                elif node.hub == self.map.goal_hub:
                    node.h = 0
                else:
                    self._heuristic(node)
                if not f_list.get((hub.id, t1)):
                    f_list.update({(hub.id, t1): node.g + node.h})

                # if shorter distance from start, update g
                if node.g < g_list.get((node.hub.id, t1), inf):
                    g_list.update({(node.hub.id, t1): node.g})
                    f_list.update({(node.hub.id, t1): g_list[
                        (node.hub.id, node.g)
                    ] + node.h})
                else:
                    continue

                # if better f cost, update
                if node.f < f_list.get(
                    (node.hub.id, node.g), inf
                ) or not node.node_in_heap(
                    hub.id, opened
                ):
                    f_list.update({(node.hub.id, node.g): node.f})
                    if not node.node_in_heap(hub.id, opened):
                        heapq.heappush(opened, (node.f, node))

        # if current hub is not goal, map has no solution
        if current.hub != self.map.goal_hub:
            raise MapError(
                "map has no reachable solution from "
                f"{self.map.start_hub.id} to {self.map.goal_hub.id}"
            )
        return current

    def hub_occupation(self, name: str, turn: int) -> int:
        """Return `name` hub occupation at `turn`"""
        if turn < 1:
            raise ValueError(f"Cannot measure occupation in {name}")
        occupation = 0
        for plan in self.plans:
            try:
                if plan[turn] == name:
                    occupation += 1
            except IndexError:
                pass
        return occupation

    def edge_traffic(self, fro: str, to: str, turn: int) -> int:
        """Return `fro`-`to` link occupation at `turn`"""
        if turn < 1 or fro == to:
            raise ValueError(f"Cannot measure traffic in {fro}-{to}")
        traffic = 0
        for plan in self.plans:
            if plan[turn - 1] == fro and plan[turn] == to:
                traffic += 1
            elif plan[turn - 1] == to and plan[turn] == fro:
                traffic += 1
        return traffic

    @staticmethod
    def _add_reservation(dict: dict[Any, int], key: Any) -> None:
        """Add 1 to `key` key in `dict`"""
        dict[key] = dict.get(key, 0) + 1

    def _update_reservations(self, node: PathNode, goal: Hub) -> None:
        """Update reservations for a single path node."""
        turn = node.g

        vertex_turn = self.reservations.vertex_occupancy
        edge_turn = self.reservations.edge_occupancy

        if turn not in vertex_turn:
            vertex_turn[turn] = {}

        if turn not in edge_turn:
            edge_turn[turn] = {}

        # in connection toward restricted hub
        if node.fro is not None:
            edge = undirected_edge(node.fro.id, node.hub.id)
            self._add_reservation(edge_turn[turn], edge)
            return

        # hub occupancy
        if node.hub.id == goal.id:
            self.delivered += 1
            vertex_turn[turn][goal.id] = self.delivered
        else:
            self._add_reservation(
                vertex_turn[turn], node.hub.id
            )

        # reserve edge if not waiting
        previous = node.next
        if previous is not None and previous.hub.id != node.hub.id:
            edge = undirected_edge(
                previous.hub.id, node.hub.id
            )
            self._add_reservation(edge_turn[turn], edge)

    def solve(self) -> str:
        """Solve the MAPF problem"""
        solution = ""
        instructions: dict[int, list[str]] = {}

        # get the movements for each drone
        for drone in self.drones:
            path: PathNode | None = self._a_star(self.map.start_hub)
            # path is backwards
            while path:
                # if hub is restricted, drone is in connection
                if path.fro:
                    drone.plan.append(f"{path.fro.id}→{path.hub.id}")
                # if hub is the same as the last one inserted, wait
                elif len(drone.plan) and path.hub.id == drone.plan[-1]:
                    drone.plan.insert(-1, "--wait--")
                else:
                    drone.plan.append(path.hub.id)
                self._update_reservations(path, self.map.goal_hub)
                path = path.next

            # reverse the path to make it time-direct
            drone.plan.reverse()
            self.plans.append(drone.plan)
            instructions.update({drone.id: drone.plan})
        n = max([len(i.plan) for i in self.drones])
        i = 1
        turn: list[str] = []
        remove: list[int] = []
        while instructions:
            for n, plan in instructions.items():
                try:
                    # don't print waiting drones
                    if plan[i] != "--wait--":
                        turn.append(f"D{n}-{plan[i]}")
                except IndexError:
                    # if plan out of range, drone delivered
                    remove.append(n)

            # remove delivered drones
            for n in remove:
                instructions.pop(n)
                if not len(instructions):
                    return solution

            # join dornes plans; newline means next turn
            move = " ".join(turn)
            solution += f"Turn {i}: " + move + "\n"

            # next turn
            i += 1
            turn.clear()
            remove.clear()
        return solution
