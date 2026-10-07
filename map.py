from models import Hub, Connection, MapData
from parser import NodeError, EdgeError


class Map:
    hubs: dict[tuple[int, int], Hub] = {}
    connections: list[Connection] = []

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
        self.add_hub(map_data.start_hub)
        hubs = map_data.hubs
        for hub in hubs.values():
            self.add_hub(hub)
        self.add_hub(map_data.end_hub)
        for edge in map_data.connections:
            self.add_connection(edge)
