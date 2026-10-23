import pygame
from pydantic import BaseModel, Field, model_validator
from exceptions import NodeError, EdgeError, MapError
from typing_extensions import Self
from enum import Enum
from math import inf


class Zone(str, Enum):
    """
    Zone types for the hubs.

    Enumeration:
        BLOCKED: No drones can traverse a hub of this kind.
        RESTRICTED: A drone takes two turns to get to a hub of this kind.
        NORMAL: A drone takes one turn to get to these kind of hubs.
        PRIORITY: Normal zones that are prioritized in pathfinding.
    """
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"


class Hub(BaseModel):
    """
    Graph vertex (also refered as node, hub or zone) as a Pydantic model.

    Arguments:
        id: the hub name.
        position: an intefer tuple containing the hub logic position.

    Keyword Arguments:
        color: A color string (defaults to "white").
        zone: The hub zone type (defaults to normal).
        capacity: How many drones can the hub hold at a time (defaults to 1).
        connections: Connections list regarding the hub (defaults to empty).
        heuristic: The intrinsic distance to the goal hub (defaults to 0).
    """
    id: str = Field(...)
    position: tuple[int, int] = Field(...)
    color: str = Field(default="white")
    zone: Zone | None = None
    capacity: int = Field(default=1, gt=0)
    connections: list[str] = []
    heuristic: float = inf

    @model_validator(mode="after")
    def validate_name(self) -> Self:
        """Raise NodeError if hub name has spaces or dashes"""
        if self.id.find(" ") >= 0 or self.id.find("-") >= 0:
            raise NodeError(f"invalid name: {self.id}")
        return self

    @model_validator(mode="after")
    def validate_color(self) -> Self:
        """Set color to white if color  not in Pygame ColorDict"""
        if self.color.lower() == "rainbow":
            return self
        try:
            pygame.Color(self.color)
        except pygame.error:
            self.color = "white"
        return self

    """@model_validator(mode="after")
    def validate_zone(self):
        if self.zone == "blocked" and self.capacity != 0:
            raise NodeError(
                f"hub {self.id} can't hold drones while being blocked"
            )
        if self.zone != "blocked" and self.capacity == 0:
            raise NodeError(
                f"hub {self.id} must hold drones if not blocked"
            )
        return self"""


class Connection(BaseModel):
    """
    Graph edge (also refered as connection or link) as a Pydantic model.

    Arguments:
        hub1: the first hub.
        hub2: the second hub.
        coords1: the logic coordinates of the first hub.
        coords2: the logic coordinates of the second hub.
        position: an intefer tuple containing the hub logic position.

    Keyword Arguments:
        capacity: How many drones can the hub hold at a time (defaults to 1).
    """
    hub1: Hub = Field(...)
    hub2: Hub = Field(...)
    coords1: tuple[int, int] = Field(...)
    coords2: tuple[int, int] = Field(...)
    capacity: int = Field(gt=0, default=1)

    @model_validator(mode="after")
    def validate_hubs(self) -> Self:
        """Raise EdgeError if hubs share name or coordinates"""
        if self.hub1.id.lower() == self.hub2.id.lower():
            raise EdgeError(
                f"{self.hub1.id}-{self.hub2.id} connects with itself"
            )
        if (self.coords1 == self.coords2):
            raise EdgeError(
                f"{self.hub1.id}-{self.hub2.id} connects the same hub"
            )
        return self


class MapData(BaseModel):
    """
    Graph as a Pydantic model.

    Arguments:
        nb_drones: Number of drones.
        start_hub: The vertex where all drones will start.
        end_hub: The vertex where all drones must go to.
        hubs: The graph vertices as a dictionary, not counting start and goal.
        connections: The graph edges as a list.
    """
    nb_drones: int = Field(gt=0)
    start_hub: Hub
    end_hub: Hub
    hubs: dict[str, Hub] = Field(...)
    connections: list[Connection] = Field(...)

    @model_validator(mode="after")
    def validate_coords(self) -> Self:
        """Raise MapError if two hubs share logical coordinates"""
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
    def validate_connections(self) -> Self:
        """Raise MapError if duplicated connections"""
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
