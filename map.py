from models import Hub, Connection
from parser import NodeError, EdgeError


class Map:
    hubs: dict[tuple[int, int], Hub] = {}
    connections: list[Connection] = []

    def add_hub(self, new: Hub) -> None:
        ids = [hub.id for hub in self.hubs.values()]
        if new.id in ids:
            raise NodeError(f"hub {new.id} already in map")
        if self.hubs.get(new.coords):
            raise AttributeError(
                f"({new.coords[0]},{new.coords[1]}) already occupied by"
                f"{self.hubs.get(new.coords)}"
            )
        self.hubs.update({new.coords: new})

    def add_connection(self, new: Connection) -> None:
        ids = [edge.id for edge in self.connections]
        if new.id in ids:
            raise EdgeError(f"connection {new.id} already in map")
        hub_ids = [hub.id for hub in self.hubs.values()]
        if new.hub1 not in hub_ids:
            raise AttributeError(f"hub not in map: {new.hub1}")
        if new.hub2 not in hub_ids:
            raise AttributeError(f"hub not in map: {new.hub2}")
        self.connections.append(new)

    def get_hub(self, name: str) -> Hub:
        for hub in self.hubs.values():
            if hub.id == name:
                return (hub)
        else:
            raise AttributeError(f"hub not in map: {name}")
