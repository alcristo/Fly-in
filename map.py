from models import Hub, Connection, MapData
from parser import NodeError, EdgeError
from typing import Any
from math import inf


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

    def get_connection(self, fro: str, to: str) -> Connection:
        for edge in self.connections:
            if edge.hub1.id == fro:
                if edge.hub2.id == to:
                    return edge
            if edge.hub2.id == fro:
                if edge.hub1.id == to:
                    return edge
        raise AttributeError(f"connection not in map: {fro}-{to}")

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
        self._g: float = 0
        self._h: float = 0
        self._f: float = 1e12
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
            self.h += 1
        elif zone == "priority":
            self.h += .8
        elif zone == "restricted":
            self.h += 2
        else:
            self.h += inf

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
    def __init__(self, level: Map, drones: list[Drone]):
        self.map = level
        self.drones = drones
        self.plans: list[list[str]] = []
        self.turns = 0

    @staticmethod
    def select_node(name: str, set: set[PathNode]) -> PathNode:
        for node in set:
            if node.hub.id == name:
                return node
        raise AttributeError(f"{name} not in set")

    def _a_star(self, start: Hub) -> PathNode:
        """Possible enhancement: sum the weight of the drones to the heuristic"""
        opened: set[PathNode] = set()
        closed: set[PathNode] = set()
        current = PathNode(start)
        opened.add(current)
        g_list: dict[str, float] = {}
        h_list: dict[str, float] = {}
        f_list: dict[str, float] = {}
        g = 0
        for _, hub in self.map.hubs.items():
            g_list.update({hub.id: 0})
            h_list.update({hub.id: inf})
            f_list.update({hub.id: g_list[hub.id] + h_list[hub.id]})
        while len(opened):
            g += 1
            current = self.select_node(current.hub.id, opened)
            opened.remove(current)
            closed.add(current)
            if current.hub.id == self.map.goal_hub:
                break
            i = 0
            for neighbour in current.hub.connections:
                hub = self.map.get_hub(neighbour)
                if PathNode.node_in_set(hub.id, closed):
                    i += 1
                    continue
                node = PathNode(self.map.get_hub(neighbour))
                node.next = current
                node.g = g
                if node.hub == self.map.start_hub:
                    node.h = inf
                elif node.hub == self.map.goal_hub:
                    node.h = 0
                else:
                    node.heuristic()
                if node.g < g_list[node.hub.id]:
                    g_list.update({node.hub.id: g})
                    f_list.update({hub.id: g_list[hub.id] + h_list[hub.id]})
                else:
                    continue
                if node.f < f_list[hub.id] or not node.node_in_set(hub.id, opened):
                    f_list.update({hub.id: node.f})
                    if not node.node_in_set(hub.id, opened):
                        opened.add(node)
        return current

#   def collision(old: Drone, new: Drone) -> bool:
#        for

    def check_plans(self, drone: Drone) -> None:
        for older in self.drones:
            if older is drone:
                break
            if "collision(older, drone)":
                self._a_star(self.map.get_hub("conflict"))
                # self._alt_a_star
                return self.check_plans(drone)

    def hub_occupation(self, name: str, turn: int) -> int:
        if turn < 1:
            raise ValueError(f"Cannot measure occupation in {name}")
        occupation = 0
        for plan in self.plans:
            if plan[turn] == name:
                occupation += 1
        return occupation

    def edge_traffic(self, fro: str, to: str, turn: int) -> int:
        if turn < 1 or fro == to:
            raise ValueError(f"Cannot measure traffic in {fro}-{to}")
        traffic = 0
        for plan in self.plans:
            if plan[turn - 1] == fro and plan[turn] == to:
                traffic += 1
        return traffic

    def check_conflicts(self, drone: Drone, plan: list[str]) -> bool:
        def vertex_conflict(drone: Drone, plan: list[str]) -> bool:
            for turn in range(len(plan)):
                name = plan[turn]
                if drone.plan[turn] == name:
                    if name == self.map.goal_hub.id:
                        return False
                    capacity = self.map.get_hub(name).capacity
                    if self.hub_occupation(name, turn + 1) + 1 == capacity:
                        return True
            return False

        def edge_conflict(drone: Drone, plan: list[str]) -> bool:
            if not vertex_conflict(drone, plan):
                return False
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
                if drone.plan[turn] == fro or drone.plan[turn - 1] == to:
                    return True
            return False

        return True in (
            vertex_conflict(drone, plan),
            edge_conflict(drone, plan),
            swap_conflict(drone, plan)
        )

    def manage_conflicts(self, drone: Drone):
        if not self.plans:
            return
        for plan in self.plans:
            if check_conflicts(drone, plan):
                if alt_route(drone, self.plans):
                    a_star_plans(turn, drone)
                else:
                    drone.plan.insert(turn - 1, "--wait--")

    def solve(self) -> str:
        solution = ""
        optimal_path = self._a_star(self.map.start_hub)
        optimal_plan: list[str] = []
        while optimal_path:
            optimal_plan.append(optimal_path.hub.id)
            optimal_path = optimal_path.next
        optimal_plan.reverse()
        for drone in self.drones:
            if not drone.plan:
                drone.plan = optimal_plan
            self.manage_conflicts(drone)
            self.plans.append(drone.plan)
        return solution
