from __future__ import annotations
from models import Hub, Connection, MapData
from exceptions import NodeError, EdgeError, MapError
from typing import Any
from math import inf
import heapq


class Map:
    drones: int = 0
    hubs: dict[str, Hub] = {}
    connections: list[Connection] = []
    start_hub: Hub
    goal_hub: Hub

    def add_hub(self, new: Hub) -> None:
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
        for edge in self.connections:
            if edge.hub1.id == fro:
                if edge.hub2.id == to:
                    return edge
            if edge.hub2.id == fro:
                if edge.hub1.id == to:
                    return edge
        raise AttributeError(f"connection not in map: {fro}-{to}")

    def hub(self, name: str) -> Hub:
        return self.hubs[name]

    def neighbours(self, name: str) -> set[str]:
        self.hubs[name]
        neighs: set[str] = set()
        for edge in self.connections:
            if name == edge.hub1.id:
                neighs.add(edge.hub2.id)
            elif name == edge.hub2.id:
                neighs.add(edge.hub1.id)
        return neighs

    def fill_map(self, map_data: MapData) -> None:
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
    def __init__(self) -> None:
        self.vertex_occupancy: dict[int, dict[str, int]] = {}
        self.edge_occupancy: dict[int, dict[tuple[str, str], int]] = {}
        # self.transitions: set[tuple[str, str, int]] = set()


def undirected_edge(u: str, v: str) -> tuple[str, str]:
    return (min((u, v)), max((u, v)))


class Drone:
    def __init__(self, number: int, start: Hub) -> None:
        self.id = number
        self.plan: list[str] = []


class PathNode:
    def __init__(self, new: Hub, fro: Hub | None = None):
        self.hub = new
        self.fro: Hub | None = None
        if new.zone == "restricted":
            self.fro = fro
        self._g: int = int(1e6)
        self._h: float = new.heuristic
        self._f: float = 1e12
        self.next: PathNode | None = None

    def __lt__(self, other: PathNode) -> bool:
        if self.g < other.g:
            return True
        return False

    def __le__(self, other: PathNode) -> bool:
        if self.g <= other.g:
            return True
        return False

    def __gt__(self, other: PathNode) -> bool:
        if self.g > other.g:
            return True
        return False

    def __ge__(self, other: PathNode) -> bool:
        if self.g >= other.g:
            return True
        return False

    def previous_hub(self) -> Hub:
        current = self.hub.id
        node = self.next
        while node:
            if node.hub.id != current:
                return node.hub
            node = node.next
        return self.hub

    def hub_in_path(self) -> bool:
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
        for node, t in set:
            if node == name and t == turn:
                return True
        return False

    @staticmethod
    def node_in_heap(name: str, heap: list[Any]) -> bool:
        for node in heap:
            if node[1].hub.id == name:
                return True
        return False

    @property
    def g(self) -> int:
        return self._g

    @g.setter
    def g(self, n: int) -> None:
        self._g = n
        self._f = self._g + self._h

    @property
    def h(self) -> float:
        return self._h

    @h.setter
    def h(self, n: float) -> None:
        self._h = n
        self._f = self._g + self._h

    @property
    def f(self) -> float:
        return self._f


class Algorithm:
    def __init__(self, level: Map):
        self.map = level
        # self.drones = drones
        self.drones: list[Drone] = []
        for i in range(level.drones):
            self.drones.append(Drone(i + 1, level.start_hub))
        self.plans: list[list[str]] = []
        self.reservations = Reservations()
        self.turns = 0

    def can_move(self, u: str, v: str, t: int) -> bool:
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
        to_occ = self.reservations.vertex_occupancy.get(t, {}).get(v, 0)
        edge_cap = self.map.get_connection(u, v).capacity
        edge_occ = self.reservations.edge_occupancy.get(t, {}).get(
            undirected_edge(u, v), 0
        )
        if to_occ >= to_cap:
            if to.zone == "restricted":
                if self.reservations.vertex_occupancy.get(
                    t + 1, {}
                ).get(v, 0) >= to_cap:
                    return False
            else:
                return False
        if edge_occ >= edge_cap:
            return False
        # if (v, u, t) in self.reservations.transitions:
        #     return False
        return True

    def _heuristic(self, node: PathNode) -> None:
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
        # init open heap and closed set
        opened: list[tuple[float, PathNode]] = []
        closed: set[tuple[str, int]] = set()
        current = PathNode(start)
        current.g = 0
        heapq.heappush(opened, (current.f, current))
        g_list: dict[tuple[str, int], float] = {}
        f_list: dict[tuple[str, int], float] = {}
        t = 0
        # g = 0
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
                # if hub currently occupied, wait
                if not self.can_move(prev.hub.id, hub.id, t1):
                    node = PathNode(prev.hub)
                    node.next = prev
                    node.g = t1
                    node.h = prev.h
                    prev = node
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
        if not dict.get(key):
            dict.update({key: 0})
        dict[key] += 1

    def _update_reservations(self, node: PathNode) -> None:
        if not self.reservations.vertex_occupancy.get(node.g):
            self.reservations.vertex_occupancy.update({node.g: {}})
        if not self.reservations.edge_occupancy.get(node.g):
            self.reservations.edge_occupancy.update({node.g: {}})
        if node.fro:
            self._add_reservation(
                self.reservations.edge_occupancy[node.g],
                undirected_edge(node.fro.id, node.hub.id)
            )
        else:
            if not node.fro:
                self._add_reservation(
                    self.reservations.vertex_occupancy[node.g], node.hub.id
                )
            self._add_reservation(
                self.reservations.edge_occupancy[node.g],
                undirected_edge(node.previous_hub().id, node.hub.id)
            )

    def _append_capacity(self, moves: list[str], turn: int) -> None:
        drone_move = moves[-1].split('-')
        if '→' in drone_move[1]:
            travel = drone_move[1].split('→')
            cap = self.map.get_connection(travel[0], travel[1]).capacity
            occ = self.reservations.edge_occupancy[turn].get(
                undirected_edge(travel[0], travel[1])
            )
        else:
            hub = drone_move[1]
            cap = self.map.hub(hub).capacity
            occ = self.reservations.vertex_occupancy[turn].get(hub, 0)
        moves[-1] += f"={occ}/{cap}"

    def solve(self, cap_info: bool = False) -> str:
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
                self._update_reservations(path)
                path = path.next
            # reverse the path to make it time-direct
            drone.plan.reverse()
            self.plans.append(drone.plan)
            instructions.update({drone.id: drone.plan})
        n = max([len(i.plan) for i in self.drones])
        if cap_info:
            for drone in self.drones:
                while len(drone.plan) < n:
                    self.reservations.vertex_occupancy[
                        len(drone.plan)
                    ][self.map.goal_hub.id] += 1
                    drone.plan.append("--wait--")
        i = 1
        turn: list[str] = []
        remove: list[int] = []
        while instructions:
            for n, plan in instructions.items():
                try:
                    # don't print waiting drones
                    if plan[i] != "--wait--":
                        turn.append(f"D{n}-{plan[i]}")
                        if cap_info:
                            self._append_capacity(turn, i)
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
