class Hub:
    def __init__(self, info: dict):
        self._id = info["id"]
        self._coords = (info["x"], info["y"])
        attr = info["attr"].split(' ')
        data = [i.split('=') for i in attr]
        self._metadata = {i[0]: i[1] for i in data}
        self._color = self._metadata.get("color", "white")
        self._zone = self._metadata.get("zone", "normal")
        assert self._zone.lower() in ("normal", "blocked", "restricted", "priority")
        self._capacity = int(self._metadata.get("max_drones", 1))
        assert self._capacity > 0
        if self._id not in ("start", "goal"):
            self._max_drones = int(self._metadata.get("max_drones", 1))
            assert self._max_drones > 0
        self._neighbours: list[Hub] = []
        self._connections: list[Connection] = []
        self._g = 0
        self._h = 0
        self._f = 0
        self._occupation: int = 0

    def add_connection(self, connection: Connection) -> None:
        if self._id not in connection._connects:
            raise ValueError(f"invalid connection: {connection._connects[0]}-{connection._connects[1]}")

    def is_full(self) -> bool:
        if (self._occupation == self._capacity):
            return True
        return False

    def _get_connection(self, hub: str) -> Connection:
        neighs = [hub._id for hub in self._neighbours]
        if hub not in neighs:
            raise ValueError(f"{hub} not neighboring {self._id}")
        

    @property
    def g(self) -> int:
        return self._g

    @g.setter
    def g(self, g: int) -> None:
        self._g = g

    @property
    def h(self) -> int:
        return self._h

    @h.setter
    def h(self, h: int) -> None:
        self._h = h

    @property
    def f(self) -> int:
        return self._f

    @f.setter
    def f(self, f: int) -> None:
        self._f = f

    @property
    def occupation(self) -> int:
        return self._occupation

    @occupation.setter
    def occupation(self, drones: int) -> None:
        self._occupation = drones


hub = {
    "coords":  (0, 0),
    "color": "red",
    "zone": "normal",
    "capacity": 1,
    "neighbours": ["hub1", "hub2", "hub3"]
}


class Start(Hub):
    def __init__(self, info: dict) -> None:
        super().self.__init__(info)
        assert self._id.find("start") >= 0
        self._max_drones = -1
        self._zone = "normal"


class Goal(Hub):
    def __init__(self, info: dict) -> None:
        super().self.__init__(info)
        assert self._id.find("goal") >= 0
        self._max_drones = -1
        self._zone = "normal"


class Connection:
    def __init__(self, info: dict):
        self._connects = (info["hub1"], info["hub2"])
        if self._connects[0] == self._connects[1]:
            raise ValueError("Connection joins hub with itself")
        attr = info.get("attr", "").split(' ')
        data = [i.split('=') for i in attr if len(i) == 2]
        if len(data) != 0:
            self._metadata = {i[0]: i[1] for i in data}
            self._max_link_capacity = self._metadata.get("max_link_capacity", 1)
            assert self._max_link_capacity > 0
        self._transiting: int = 0
        hubs: None | tuple[Hub, Hub] = None

    def get_hubs(self, hubs: list[Hub]) -> None:
        for hub in hubs:
            if hub._id == self._connects[0]:
                hub1 = hub
                break
        else:
            raise AttributeError("Hub 1 not found")
        for hub in hubs:
            if hub._id == self._connects[1]:
                hub2 = hub
                break
        else:
            raise AttributeError("Hub 2 not found")
        self._hubs = (hub1, hub2)

    @property
    def transiting(self) -> int:
        return self._transiting

    @transiting.setter
    def transiting(self, drones: int) -> None:
        self._transiting = drones


connection = {
    "connects": ("hub1", "hub2"),
    "capacity": 1
}


class Map:
    def __init__(
        self,
        drones: int,
        hubs: list[Hub],
        connections: list[Connection]
    ) -> None:
        self._num = drones
        self._hubs = hubs
        self._ids = [hub._id for hub in hubs]
        self._connections = connections
        for name in self._ids:
            if name.lower().find("start") >= 0:
                self._start = self._hubs[self._ids.index(name)]
                break
        else:
            raise ValueError("Start hub not found")
        for name in self._ids:
            if name.lower().find("goal") >= 0:
                self._goal = self._hubs[self._ids.index(name)]
                break
        else:
            raise ValueError("Goal hub not found")
        for i in self._connections:
            if i._connects[0] in self._ids and i._connects[1] in self._ids:
                a, b = i._connects
                hub_a = self._hubs[self._get_hub_index(a)]
                hub_b = self._hubs[self._get_hub_index(b)]
                hub_a._neighbours.append(hub_b)
                hub_b._neighbours.append(hub_a)
            else:
                raise ValueError(f"Invalid connection: {i._connects[0]}-{i._connects[1]}")
        for hub in self._hubs:
            for way in self._connections:
                if hub._id in way._connects:
                    hub._neighbours.append(self._hubs[self._get_hub_index(self._neighbour(way._connects, hub._id))])
                    hub._connections.append(way)

    def _neighbour(way: tuple[str, str], hub: str) -> int:
        if hub not in tuple:
            raise ValueError(f"Invalid connection: {i._connects[0]}-{i._connects[1]}")
        if hub == way[0]:
            return 0
        return 1

    def add_hub(self, hub: Hub) -> None:
        if hub._id not in [hub._id for hub in self._hubs]:
            self._hubs.append(hub)

    def _get_hub_index(self, hub_name: str) -> int:
        for i in range(len(self._hubs)):
            if self._hubs[i]._id == hub_name:
                return i
        else:
            raise ValueError("Hub not in map")

    def add_connection(self, connection: Connection) -> None:
        a, b = connection._connects
        if connection._id not in [way._id for way in self._connections]:
            if False not in [hub._id in self._hubs for hub in (a, b)]:
                self._connections.append(connection)
                hub_a = self._hubs[self._get_hub_index(a._id)]
                hub_b = self._hubs[self._get_hub_index(b._id)]
                hub_a._neighbours.append(hub_b)
                hub_b._neighbours.append(hub_a)


class Drone:
    def __init__(self, start: Start) -> None:
        self._current: Hub = start
        self._goingto: Hub | None = None
        self._transiting: Connection | None = None

    def _go_to(self, to: Hub):
        neighs = [hub._id for hub in self._current._neighbours]
        if to._id not in neighs:
            raise ValueError(f"{hub._id} not neighboring {self._current._id}")
        if to._zone == "blocked":
            raise ValueError(f"blocked hub: {to._id}")
        if to._zone == "restricted" and not transiting:
            
        if to._occupation == to._capacity:
            pass # more if gonna be free


class Simulation:
    def __init__(self, map: Map, drones: int, start: Hub = None, goal: Hub = None) -> None:
        self._map = map
        self._drones = [Drone]
        self._start = self._map._hubs