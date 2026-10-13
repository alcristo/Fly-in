from __future__ import annotations
from models import Hub, Connection, MapData
from exceptions import NodeError, EdgeError, MapError
from typing import Any
from math import inf, sqrt
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

    def fill_map(self, map_data: MapData):
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
        open_heap: list[tuple[int, str]] = []
        cl_set: set[str] = set()
        current: str = self.goal_hub.id
        heapq.heappush(open_heap, (0, current))
        while len(open_heap):
            dist, current = heapq.heappop(open_heap)
            cl_set.add(current)
            neighbours = self.neighbours(current)
            for hub in neighbours:
                if hub in cl_set:
                    continue
                zone = 1
                if self.hub(hub).zone == "restricted":
                    zone = 2
                heapq.heappush(open_heap, (dist + 1 + zone, hub))
        for h, hub in open_heap:
            self.hub(hub).heuristic = h


class Reservations:
    def __init__(self) -> None:
        self.vertex_occupancy: dict[int, dict[str, int]] = {}
        self.edge_occupancy: dict[int, dict[tuple[str, str], int]] = {}
        self.transitions: set[tuple[str, str, int]] = set()


def undirected_edge(u: str, v: str) -> tuple[str, str]:
    return (min((u, v)), max((u, v)))


class Drone:
    def __init__(self, number: int, start: Hub) -> None:
        self.id = number
        self.plan: list[str] = []
        self.current: Hub = start
        self.goingto: Hub | None = None
        self.transiting: Connection | None = None


class PathNode:
    def __init__(self, new: Hub, fro: Hub | None = None):
        self.hub = new
        self.fro: Hub | None = None
        if new.zone == "restricted":
            self.fro = fro
        self._g: float = inf
        self._h: float = new.heuristic
        self._f: float = 1e12
        self.next: PathNode | None = None

    def __lt__(self, other: PathNode) -> bool:
        return False

    def __le__(self, other: PathNode) -> bool:
        return False

    def __gt__(self, other: PathNode) -> bool:
        return False

    def __ge__(self, other: PathNode) -> bool:
        return False

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
    def node_in_set(name: str, set: set[Any]) -> bool:
        for node in set:
            if node.hub.id == name:
                return True
        return False

    @staticmethod
    def node_in_heap(name: str, heap: list[Any]) -> bool:
        for node in heap:
            if node[1].hub.id == name:
                return True
        return False

    @property
    def g(self) -> float:
        return self._g

    @g.setter
    def g(self, n: float) -> None:
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

    @staticmethod
    def _select_node(name: str, set: set[PathNode]) -> PathNode:
        for node in set:
            if node.hub.id == name:
                return node
        raise AttributeError(f"{name} not in set")

    def _occupied(self, fro: Hub, to: Hub, turn: int) -> bool:
        occupation = 0
        occupied = {"zone": False, "link": False}
        # check vertex conflicts
        for plan in self.plans:
            try:
                if plan[turn] == to.id:
                    occupation += 1
                    if occupation == to.capacity:
                        occupied["zone"] = True
                        break
            except IndexError:
                pass
        occupation = 0
        link = self.map.get_connection(fro.id, to.id)
        # check edge conflicts
        for plan in self.plans:
            try:
                # direct transit
                if plan[turn] == to.id and plan[turn - 1] == fro.id:
                    occupation += 1
                    if occupation == link.capacity:
                        occupied["link"] = True
                        break
                # reverse transit
                elif plan[turn] == fro.id and plan[turn - 1] == to.id:
                    occupation += 1
                    if occupation == link.capacity:
                        occupied["link"] = True
                        break
                # restricted transit
                elif plan[turn] == to.id and fro.id in plan[turn - 1].split('-'):
                    if occupation == link.capacity:
                        occupied["link"] = True
                        break
            except IndexError:
                pass
        return True in occupied.values()

    def can_move(self, u: str, v: str, t: int):
        to = self.map.hub(v)
        to_cap = to.capacity
        edge_cap = self.map.get_connection(u, v).capacity
        if self.reservations.vertex_occupancy.get(t, {}).get(v, 0) >= to_cap:
            return False
        if self.reservations.edge_occupancy.get(t, {}).get(
            undirected_edge(u, v), 0
        ) >= edge_cap:
            return False
        if (v, u, t) in self.reservations.transitions:
            return False
        return True

    def _euclid(self, hub: Hub) -> float:
        coords = hub.position
        end = self.map.goal_hub.position
        sq_dist = (end[0] - coords[0])**2 + (end[1] - coords[1])**2
        return sqrt(sq_dist)

    def _next_turn_free(self, fro: Hub, to: Hub, since: int) -> int:
        plan_len = [len(plan) for plan in self.plans]
        for i in range(since, max(plan_len)):
            if not self._occupied(fro, to, i):
                if to.zone == "restricted":
                    return min((abs(i - since), abs(i - since - 1)))
                else:
                    return i - since
        return max(plan_len) - since

    def _heuristic(self, node: PathNode) -> None:
        occupancy = self.hub_occupation(node.hub.id, int(node.g))
        node.h = node.hub.heuristic + occupancy / node.hub.capacity
        if node.hub_in_path():
            node.h += 5
        zone = node.hub.zone
        if zone == "normal":
            node.h += 1
        elif zone == "priority":
            node.h += .9
        elif zone == "restricted":
            node.h += 2
        else:
            node.h += inf

    def _all_neighbours_occupied(self, fro: Hub, turn: int) -> bool:
        if fro == self.map.goal_hub:
            return False
        neighbours = self.map.neighbours(fro.id)
        if not len(neighbours):
            return False
        for name in neighbours:
            to = self.map.hub(name)
            if not self._occupied(fro, to, turn):
                return False
        return True

    def _a_star(self, start: Hub) -> PathNode:
        """Possible enhancement: sum the weight of the drones to the heuristic"""
        # init open heap and closed set
        opened: list[tuple[float, PathNode]] = []
        closed: set[PathNode] = set()
        current = PathNode(start)
        current.g = 0
        heapq.heappush(opened, (current.f, current))
        g_list: dict[str, float] = {}
        f_list: dict[str, float] = {}
        g = 0
        # init g & f score dictionaries
        for name, hub in self.map.hubs.items():
            g_list.update({name: inf})
            f_list.update({name: g_list[name] + hub.heuristic})
        # while nodes in open heap
        while len(opened):
            g = int(current.g) + 1
            current = heapq.heappop(opened)[1]
            closed.add(current)
            # just a patch; need to resolve this issue for easy 02 later
            if current.next and self._occupied(current.next.hub, current.hub, g):
                current.g += 1
                heapq.heappush(opened, (current.f, current))
                continue
            # if current is goal, exit
            if current.hub.id == self.map.goal_hub.id:
                return current
            # if all neighbours occupied, wait
            while self._all_neighbours_occupied(current.hub, g):
                g += 1
                node = PathNode(current.hub)
                node.next = current
                node.g = g
                current = node
            # check neighbours
            for neighbour in current.hub.connections:
                hub = self.map.hub(neighbour)
                if hub.zone == "blocked":
                    continue
                if PathNode.node_in_set(hub.id, closed):
                    continue
                # if occupied neighbour, check when it's gonna be free
                if self._occupied(current.hub, hub, g):
                    free_in = self._next_turn_free(current.hub, hub, g)
                    node = current
                    for _ in range(free_in):
                        wait = PathNode(node.hub)
                        wait.next = node
                        wait.g = node.g + 1
                        node = wait
                # if restricted neighbour, occupy link
                if hub.zone == "restricted":
                    r_node = PathNode(hub, current.hub)
                    r_node.next = current
                    r_node.g = current.g + 1
                    node = PathNode(hub)
                    node.next = r_node
                    node.g = r_node.g + 1
                else:
                    node = PathNode(hub)
                    node.next = current
                    node.g = g
                # compute heuristics
                if node.hub == self.map.start_hub:
                    node.h = inf
                elif node.hub == self.map.goal_hub:
                    node.h = 0
                else:
                    self._heuristic(node)
                # if shorter distance from start, update g
                if node.g < g_list[node.hub.id]:
                    g_list.update({node.hub.id: g})
                    f_list.update({hub.id: g_list[hub.id] + node.h})
                else:
                    continue
                # if better f cost, update
                if node.f < f_list[hub.id] or not node.node_in_heap(
                    hub.id, opened
                ):
                    f_list.update({hub.id: node.f})
                    if not node.node_in_heap(hub.id, opened):
                        heapq.heappush(opened, (node.f, node))
        # if current hub is not goal, map has no solution
        if current.hub != self.map.goal_hub:
            raise MapError(
                "map has no reachable solution from "
                f"{self.map.start_hub.id} to {self.map.goal_hub.id}"
            )
        return current

    def check_plans(self, drone: Drone) -> None:
        for older in self.drones:
            if older is drone:
                break
            if "collision(older, drone)":
                self._a_star(self.map.hub("conflict"))
                # self._alt_a_star
                return self.check_plans(drone)

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

    def check_conflicts(self, drone: Drone, plan: list[str]) -> bool:
        def vertex_conflict(drone: Drone, plan: list[str]) -> bool:
            for turn in range(len(plan)):
                name = plan[turn]
                if drone.plan[turn] == name:
                    if name == self.map.goal_hub.id:
                        return False
                    capacity = self.map.hub(name).capacity
                    if self.hub_occupation(name, turn + 1) + 1 == capacity:
                        return True
            return False

        def edge_conflict(drone: Drone, plan: list[str]) -> bool:
            for turn in range(1, len(plan)):
                fro = plan[turn]
                to = plan[turn + 1]
                if drone.plan[turn] == fro and drone.plan[turn + 1] == to:
                    capacity = self.map.get_connection(fro, to).capacity
                    if self.edge_traffic(fro, to, turn) + 1 == capacity:
                        return True
            return False

        def swap_conflict(drone: Drone, plan: list[str]) -> bool:
            for turn in range(1, len(plan)):
                fro = plan[turn - 1]
                to = plan[turn]
                if drone.plan[turn] == fro and drone.plan[turn - 1] == to:
                    return True
            return False

        return True in (
            vertex_conflict(drone, plan),
            edge_conflict(drone, plan),
            swap_conflict(drone, plan)
        )

    """def manage_conflicts(self, drone: Drone):
        if not self.plans:
            return
        for plan in self.plans:
            if self.check_conflicts(drone, plan):
                if alt_route(drone, self.plans):
                    a_star_plans(turn, drone)
                else:
                    drone.plan.insert(turn - 1, "--wait--")"""

    def solve(self) -> str:
        solution = ""
        instructions: dict[int, list[str]] = {}
        # get the movements for each drone
        for drone in self.drones:
            path: PathNode | None = self._a_star(self.map.start_hub)
            # path is backwards
            while path:
                # if hub is the same as the last one inserted, wait
                if len(drone.plan) and path.hub.id == drone.plan[-1]:
                    drone.plan.insert(-1, "--wait--")
                # if hub is restricted, drone is in connection
                elif path.fro:
                    drone.plan.append(f"{path.fro}.{path.hub}")
                else:
                    drone.plan.append(path.hub.id)
                path = path.next
            # reverse the path to make it time-direct
            drone.plan.reverse()
            self.plans.append(drone.plan)
            instructions.update({drone.id: drone.plan})
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
