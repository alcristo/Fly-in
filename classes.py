from .pygame_test import rainbow
from pydantic import BaseModel, Field, model_validator, ValidationError
import pygame
import sys


class ParsingError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class Hub(BaseModel):
    id: str = Field(...)
    coords: tuple[int, int] = Field(...)
    color: str = Field(...)
    zone: str = Field(default="normal")
    capacity: int = Field(default=1, gt=0)
    # self._neighbours: list[Hub] = []

    @model_validator(mode="after")
    def validate_name(self):
        if self.id.find(" ") >= 0 or self.id.find("-") >= 0:
            raise ValidationError(f"invalid name: {self.id}")
        return self

    @model_validator(mode="after")
    def validate_color(self):
        if self.color.lower() == "rainbow":
            return self
        try:
            pygame.Color(self.color)
        except pygame.error:
            raise ValidationError(f"invalid color name: {self.color}")
        return self

    @model_validator(mode="after")
    def validate_zone(self):
        if self.zone.lower() not in (
            "normal", "restricted", "priority", "blocked"
        ):
            raise ValidationError(f"invalid zone type: {self.zone}")
        return self


class Connection(BaseModel):
    id: str = Field(...)
    hub1: str = Field(...)
    hub2: str = Field(...)
    coords1: tuple[int, int] = Field(...)
    coords2: tuple[int, int] = Field(...)
    capacity: int = Field(gt=0, default=1)

    @model_validator(mode="after")
    def validate_name(self):
        if self.id.find(" ") >= 0 or self.id.find("-") >= 0:
            raise ValidationError(f"invalid name: {self.id}")
        return self

    @model_validator(mode="after")
    def validate_hubs(self):
        if self.hub1.lower() == self.hub2.lower():
            raise ValidationError(
                f"{self.id} connects {self.hub1} with itself"
            )
        return self

    @model_validator(mode="after")
    def validate_coords(self):
        if (self.coords1 == self.coords2):
            raise ValidationError(f"{self.id} connects the same hub")
        return self


class Map(BaseModel):
    hubs: dict[tuple[int, int], Hub] = {}
    connections: list[Connection] = []

    def add_hub(self, new: Hub) -> None:
        ids = [hub.id for hub in self.hubs.values()]
        if new.id in ids:
            raise ValidationError(f"hub {new.id} already in map")
        if self.hubs.get(new.coords):
            raise AttributeError(
                f"({new.coords[0]},{new.coords[1]}) already occupied by"
                f"{self.hubs.get(new.coords)}"
            )
        self.hubs.update({new.coords: new})

    def add_connection(self, new: Connection) -> None:
        ids = [way.id for way in self.connections]
        if new.id in ids:
            raise ValidationError(f"connection {new.id} already in map")
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


class Screen(pygame.Surface):
    def __init__(self, w: int, h: int, level: Map):
        super().__init__((w, h))
        self.map: Map = level
        self.cam_x: float = 0
        self.cam_y: float = 0
        self.zoom: float = 1.0
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.world_x: float = self.mouse_x / self.zoom + self.cam_x
        self.world_y: float = self.mouse_y / self.zoom + self.cam_y
        self.drag: bool = False

    def draw(self, scale: int) -> None:
        for way in self.map.connections:
            hub1 = self.map.get_hub(way.hub1)
            hub2 = self.map.get_hub(way.hub2)
            pygame.draw.line(self, "white", hub1.coords, hub2.coords, 4)
            pygame.draw.line(self, "black", hub1.coords, hub2.coords, 2)
        rb = rainbow()
        for hub in self.map.hubs.values():
            if (hub.color.lower() == "rainbow"):
                pygame.draw.circle(self, rb(2), hub.coords, 10)
            else:
                pygame.draw.circle(self, hub.color.lower(), hub.coords, 10)
            pygame.draw.circle(self, "black", hub.coords, 10, 2)

    """def pan(self)

    def zoom(self, mul: float)"""


class Parser:

    def __init__(self, map: str) -> None:
        # Open the map file
        try:
            with open(map) as f:
                txt = f.read().strip()
                lines = txt.split("\n")
                while "" in lines:
                    lines.remove("")
                valid = [i.split(':') for i in lines if i.find('#') != 0]
        except FileNotFoundError as e:
            print(e)
            sys.exit()
        except PermissionError as e:
            print(e)
            sys.exit()

        # Check existence of nb_drones, hubs and connections
        try:
            if valid[0][0].lower() != "nb_drones":
                raise ParsingError("Number of drones is not defined")
            for i in valid:
                if i[0].lower() == "nb_drones":
                    break
            else:
                raise ParsingError("Number of drones is not defined")
            for i in valid:
                if i[0].find("hub") >= 0:
                    break
            else:
                raise ParsingError("No hubs in the map")
            for i in valid:
                if i[0].lower() == "connection":
                    break
            else:
                raise ParsingError("No connections in the map")
        except ParsingError as e:
            print(e)
            sys.exit()

        # Save the hubs and connections
        self.hubs, self.connections = [], []
        try:
            for i in valid:
                if i[0].lower() == "nb_drones":
                    nb = int(i[1])
                    assert nb > 0 and nb < 1000
                elif i[0].lower().find("hub") >= 0:
                    lst = i[1].strip().split(' ')
                    hub: dict[str, str] = {
                        "id": lst[0],
                        "x": lst[1],
                        "y": lst[2],
                        "attr": ' '.join(lst[3:]).lstrip('[').rstrip(']')
                    }
                    if hub["attr"] == "":
                        hub.pop("attr")
                    if hub["id"].find("-") >= 0:
                        raise ParsingError(f"Invalid name for zone: {hub['id']}")
                    self.hubs.append(hub)
                elif i[0].lower() == "connection":
                    lst = i[1].strip().split(' ')
                    hubs = lst[0].strip().split('-')
                    if hubs[0] == hubs[1]:
                        raise ParsingError(f"Connection with itself: {hubs[0]}")
                    connection = {
                        "hub1": hubs[0],
                        "hub2": hubs[1],
                        "attr": ' '.join(lst[1:]).lstrip('[').rstrip(']')
                    }
                    ids = [i.get("id") for i in hubs]
                    if connection["hub1"] not in ids:
                        raise ParsingError(f"Hub {connection['hub1']} not defined")
                    if connection["hub2"] not in ids:
                        raise ParsingError(f"Hub {connection['hub2']} not defined")
                    if connection in self.connections or {
                        "hub1": connection["hub2"], "hub2": connection["hub1"]
                    } in self.connections:
                        raise ParsingError(f"Duplicated connection: {connection}")
                    if connection["attr"] == "":
                        connection.pop("attr")
                    self.connections.append(connection)
            for i in hubs:
                if i["id"].find("start") >= 0:
                    break
            else:
                raise ParsingError("No start hub")
            for i in hubs:
                if i["id"].find("goal") >= 0:
                    break
            else:
                raise ParsingError("No goal hub")
            for i in hubs:
                for j in hubs[hubs.index(i):]:
                    if i["id"] == j["id"] and i is not j:
                        raise ValueError(f"Hubs with identical name: {i['id']}")
                    if i["id"] == j["id"] and i is not j:
                        raise ValueError(f"Hubs with identical name: {i['id']}")
        except ValueError as e:
            print(e)
        except IndexError:
            print("Invalid variable separation")
        except AssertionError:
            print("Invalid number of drones")
        except ParsingError as e:
            print(e)


hub = {
    "coords":  (0, 0),
    "color": "red",
    "zone": "normal",
    "capacity": 1,
    "neighbours": ["hub1", "hub2", "hub3"]
}


connection = {
    "connects": ("hub1", "hub2"),
    "capacity": 1
}
"""

"""
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
