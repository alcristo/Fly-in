# from .pygame_test import rainbow
import pygame
from pydantic import BaseModel, Field, model_validator
from exceptions import NodeError, EdgeError, MapError
from enum import Enum
from typing import Any


class Zone(str, Enum):
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"


class Hub(BaseModel):
    id: str = Field(...)
    position: tuple[int, int] = Field(...)
    color: str = Field(default="white")
    zone: Zone | None = None
    capacity: int = Field(default=1, gt=0)
    occupation: int = 0
    connections: list[str] = []
    heuristic: int = 0

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
