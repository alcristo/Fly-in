from models import Hub, Connection, MapData
from parser import NodeError, EdgeError
from typing import Any


class Map:
    hubs: dict[tuple[int, int], Hub] = {}
    connections: list[Connection] = []
    start_hub: Hub
    goal_hub: Hub

    def add_hub(self, new: Hub) -> None:
        ids = [hub.id for hub in self.hubs.values()]
        if new.id in ids:
            raise NodeError(f"hub {new.id} already in map")
        if self.hubs.get(new.position):
            raise AttributeError(
                f"({new.position[0]},{new.position[1]}) already occupied by"
                f"{self.hubs.get(new.position)}"
            )
        self.hubs.update({new.position: new})

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

    def get_hub(self, name: str) -> Hub:
        for hub in self.hubs.values():
            if hub.id == name:
                return (hub)
        else:
            raise AttributeError(f"hub not in map: {name}")

    def fill_map(self, map_data: MapData):
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


class Drone:
    def __init__(self, number: int, start: Hub) -> None:
        self.id = number
        self.plan: list[str] = []
        self.current: Hub = start
        self.goingto: Hub | None = None
        self.transiting: Connection | None = None


class PathNode:
    def __init__(self, new: Hub):
        self.hub = new
        self._g: int = 0
        self._h: int = 0
        self._f: int = int(1e12)
        self.next: Any = None

    @staticmethod
    def node_in_set(name: str, set: set[Any]) -> bool:
        for node in set:
            if node.hub.id == name:
                return True
        return False

    def heuristic(self) -> None:
        if self.hub.is_occupied():
            self.h = 100
            return
        zone = self.hub.zone
        if zone == "normal":
            self.h = 0
        elif zone == "priority":
            self.h = -1
        elif zone == "restricted":
            self.h = 1
        else:
            self.h = int(1e6)

    @property
    def g(self) -> int:
        return self._g

    @g.setter
    def g(self, n: int) -> None:
        self._g = n
        self._f = self._g + self._h

    @property
    def h(self) -> int:
        return self._h

    @h.setter
    def h(self, n: int) -> None:
        self._h = n
        self._f = self._g + self._h

    @property
    def f(self) -> int:
        return self._f


class Algorithm:
    def __init__(self, level: Map, drones: list[Drone]):
        self.map = level
        self.drones = drones
        self.turns = 0

    @staticmethod
    def select_node(name: str, set: set[PathNode]) -> PathNode:
        for node in set:
            if node.hub.id == name:
                return node
        raise AttributeError(f"{name} not in set")

    def _a_star(self, drone: Drone) -> PathNode:
        opened: set[PathNode] = set()
        closed: set[PathNode] = set()
        current = PathNode(drone.current)
        opened.add(current)
        g_list: list[int] = []
        h_list: list[int] = []
        g = 0
        while len(opened):
            g += 1
            for _ in range(len(drone.current.connections)):
                g_list.append(0)
                h_list.append(int(1e6))
            current = self.select_node(drone.current.id, opened)
            opened.remove(current)
            closed.add(current)
            if drone.current.id == self.map.goal_hub:
                break
            i = 0
            for neighbour in drone.current.connections:
                hub = self.map.get_hub(neighbour)
                if PathNode.node_in_set(hub.id, closed):
                    i += 1
                    continue
                node = PathNode(self.map.get_hub(neighbour))
                node.next = current
                node.g = g
                if node.hub == self.map.start_hub:
                    node.h = 1000
                elif node.hub == self.map.goal_hub:
                    node.h = -1000
                else:
                    node.heuristic()
                if node.g < hub.g:
                    node.hub.g = g
                else:
                    continue
                if node.f < hub.f or not node.node_in_set(hub.id, opened):
                    hub.f = node.f
                    if not node.node_in_set(hub.id, opened):
                        opened.add(node)
        return current


    def solve(self) -> str:
        solution = ""
        while len(self.drones):
            for drone in self.drones:
                if not drone.plan:
                    optimal_path = self._a_star(drone)
                    while optimal_path:
                        drone.plan.append(optimal_path.hub.id)
                        optimal_path = optimal_path.next
                    drone.plan.reverse()
        return solution
