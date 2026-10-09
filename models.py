# from .pygame_test import rainbow
import pygame
from pydantic import BaseModel, Field, model_validator
from exceptions import NodeError, EdgeError, MapError
from enum import Enum
from typing import Any


"""
class Position:
    def __init__(self, pos: tuple[int, int]) -> None:
        self.x = pos[0]
        self.y = pos[1]
"""


class Zone(str, Enum):
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"


class Hub(BaseModel):
    id: str = Field(...)
    # position: Position = Field(...)
    position: tuple[int, int] = Field(...)
    color: str = Field(default="white")
    zone: Zone | None = None
    capacity: int = Field(default=1, gt=0)
    occupation: int = 0
    connections: list[str] = []
    _g: float = 0
    _h: float = 1000
    _f: float = 1000

    @model_validator(mode="after")
    def validate_name(self):
        if self.id.find(" ") >= 0 or self.id.find("-") >= 0:
            raise NodeError(f"invalid name: {self.id}")
        return self

    @model_validator(mode="after")
    def validate_color(self):
        if self.color.lower() == "rainbow":
            return self
        try:
            pygame.Color(self.color)
        except pygame.error:
            self.color = "white"
        return self

    @model_validator(mode="after")
    def validate_zone(self):
        if self.zone == "blocked" and self.capacity != 0:
            raise NodeError(
                f"hub {self.id} can't hold drones while being blocked"
            )
        if self.zone != "blocked" and self.capacity == 0:
            raise NodeError(
                f"hub {self.id} must hold drones if not blocked"
            )
        return self

    def is_occupied(self) -> bool:
        return self.occupation >= self.capacity

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

    @f.setter
    def f(self, n: float) -> None:
        self._f = n


class Connection(BaseModel):
    hub1: Hub = Field(...)
    hub2: Hub = Field(...)
    coords1: tuple[int, int] = Field(...)
    coords2: tuple[int, int] = Field(...)
    capacity: int = Field(gt=0, default=1)
    occupation: int = 0

    @model_validator(mode="after")
    def validate_hubs(self):
        if self.hub1.id.lower() == self.hub2.id.lower():
            raise EdgeError(
                f"{self.hub1.id}-{self.hub2.id} connects with itself"
            )
        if (self.coords1 == self.coords2):
            raise EdgeError(
                f"{self.hub1.id}-{self.hub2.id} connects the same hub"
            )
        return self

    @model_validator(mode="after")
    def validate_link(self):
        if self.capacity < 1:
            self.capacity = 1
        return self

    def is_occupied(self) -> bool:
        return self.occupation >= self.capacity


"""
class Scene(pygame.Surface):
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
        self._rainbow = rainbow()

    def draw_map(self, scale: int) -> None:
        for edge in self.map.connections:
            hub1 = self.map.get_hub(edge.hub1)
            hub2 = self.map.get_hub(edge.hub2)
            pygame.draw.line(self, "white", hub1.coords, hub2.coords, 4)
            pygame.draw.line(self, "black", hub1.coords, hub2.coords, 2)
        for hub in self.map.hubs.values():
            if hub.color.lower() == "rainbow":
                pygame.draw.circle(self, self._rainbow(2), hub.coords, 10)
            else:
                pygame.draw.circle(self, hub.color.lower(), hub.coords, 10)
            pygame.draw.circle(self, "black", hub.coords, 10, 2)

    def pan(self)

    def zoom(self, mul: float)
"""


class Validator:

    @classmethod
    def map_element(cls, element: str) -> None:
        if element not in (
            "hub", "start_hub", "end_hub", "connection", "nb_drones"
        ):
            raise NodeError(f"invalid level element: {element}")

    @classmethod
    def num(cls, n: str) -> bool:
        try:
            int(n)
        except ValueError:
            return False
        return True

    @classmethod
    def hub_name(cls, name: str) -> bool:
        if name.find('-') >= 0 or name.find(' ') >= 0:
            return False
        return True

    @classmethod
    def drone_number(cls, n: int) -> bool:
        if n < 1 or n > 1000:
            return False
        return True

    @classmethod
    def zone(cls, zone_type: str) -> None:
        if zone_type not in ("normal", "restricted", "priority", "blocked"):
            raise NodeError(f"invalid zone type: {zone_type}")

    @classmethod
    def connection(cls, zone_type: str) -> None:
        if zone_type not in ("normal", "restricted", "priority", "blocked"):
            raise EdgeError(f"invalid zone type: {zone_type}")

    @classmethod
    def list_len(cls, it: list[Any], n: int) -> bool:
        return len(it) == n

    @classmethod
    def complete_hub(cls, hub: dict[str, str]) -> None:
        if not (hub.get("color")):
            hub.update({"color": "white"})
        if not hub.get("zone"):
            hub.update({"zone": "normal"})
        else:
            cls.zone(hub["zone"])
        if not hub.get("max_drones"):
            hub.update({"max_drones": "1"})
        else:
            cls.num(hub["max_drones"])


class MapData(BaseModel):
    nb_drones: int = Field(gt=0)
    start_hub: Hub
    end_hub: Hub
    hubs: dict[str, Hub] = Field(...)
    connections: list[Connection] = Field(...)

    @model_validator(mode="after")
    def validate_coords(self):
        hubs: list[Hub] = []
        hubs.append(self.start_hub)
        for hub in self.hubs.values():
            hubs.append(hub)
        hubs.append(self.end_hub)
        for i in range(len(hubs)):
            for j in range(i + 1, len(hubs)):
                if hubs[i].position == hubs[j].position:
                    raise MapError(
                        f"{hubs[i].id} and {hubs[j].id} "
                        f"share coordinates: {hubs[i].position}",
                    )
        return self

    @model_validator(mode="after")
    def validate_connections(self):
        for i in range(len(self.connections)):
            for j in range(i + 1, len(self.connections)):
                dup = [
                    self.connections[i].hub1 == self.connections[j].hub2,
                    self.connections[j].hub1 == self.connections[i].hub2
                ]
                if False not in dup:
                    raise MapError(
                        "duplicated connection: "
                        f"{self.connections[i].hub1.id}-"
                        f"{self.connections[i].hub2.id}"
                    )
        return self


"""
class Simulation:
    def __init__(
        self, level: Map, drones: int, start: Hub = None, goal: Hub = None
    ) -> None:
        self._map = level
        self._drones: list[Drone] = drones
        self._start = self._map._hubs
"""
