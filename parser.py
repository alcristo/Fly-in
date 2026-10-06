from models import MapData


class ParsingError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class NodeError(ParsingError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class EdgeError(ParsingError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MapError(ParsingError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class Parser:

    def parse(self, path: str):
        try:
            with open(path) as f:
                txt = f.read().strip()
        except FileNotFoundError:
            raise ParsingError(f"{path}: file not found")
        except PermissionError:
            raise ParsingError(f"{path}: permission denied")
        lines = txt.split('\n')
        while "" in lines:
            lines.remove("")
        valid_lines = [
            line.split(':') for line in lines if line.find('#') != 0
        ]
        start_hub, end_hub = {}, {}
        for line in valid_lines:
            if (len(line) != 2):
                raise ParsingError(f"invalid line: {line}")
            if line[0] not in (
                "nb_drones", "start_hub", "end_hub", "hub", "connection"
            ):
                raise ParsingError(f"invalid line: {line}")
            if line[0] == "nb_drones":
                nb_drones = int(line[1])
            elif line[0] == "start_hub":
                if len(start_hub.keys()):
                    raise ParsingError("more than one start hub in map")
                start_hub = self.parse_zone(line[1], "start_hub")
            elif line[0] == "end_hub":
                if len(end_hub.keys()):
                    raise ParsingError("more than one end hub in map")
                end_hub = self.parse_zone(line[1], "end_hub")
            elif line[0] == "hub":
                hubs.append(self.parse_zone(line[1], "hub"))
            elif line[0] == "connection":
                connections.append(self.parse_edge(line[1], "connection"))
        if not start_hub:
            raise NodeError("start hub not found")
        if not end_hub:
            raise NodeError("goal hub not found")
        return MapData(nb_drones=nb_drones, hubs=)

    def validate_hubs(self):
        for i in range(len(self.hubs)):
            for j in range(i, len(self.hubs)):
                if self.hubs[i].
        return self

    def parse_zone(self, line: str, element: str) -> dict[str, str]:
        line.strip()
        inst: dict[str, str] = {}
        metadata = line.split(' ')
        if len(metadata) < 3:
            raise ParsingError(f"invalid line: {element}: {line}")
        inst.update({"id": metadata[0]})
        try:
            assert inst["id"].find('-') < 0
        except AssertionError:
            raise ParsingError(f"invalid hub name: {inst['id']}")
        inst.update({"x": metadata[1]})
        inst.update({"y": metadata[2]})
        try:
            int(inst["x"])
            int(inst["y"])
        except ValueError:
            raise ParsingError(
                f"invalid coordinates for {inst['id']}: "
                f"{inst['x'], inst['y']}"
            )
        attr: list[list[str]] = []
        for data in metadata[3:]:
            attr.append(data.lstrip('[').rstrip(']').split('='))
        for att in attr:
            if att[0] not in ("color", "zone", "max_drones"):
                continue
            elif att[0] == "max_drones":
                if element == "hub":
                    inst.update({"max_drones": att[1]})
                else:
                    inst.update({"max_drones": "1000"})
            else:
                inst.update({att[0]: att[1]})
        if not inst.get("color"):
            inst.update({"color": "white"})
        if not inst.get("zone"):
            inst.update({"zone": "normal"})
        else:
            try:
                assert inst["zone"] in (
                    "normal", "priority", "restricted", "blocked"
                )
            except AssertionError:
                raise ParsingError(
                    f"invalid zone type for {inst['id']}"
                    f": {inst['zone']}"
                )
        if not inst.get("max_drones"):
            inst.update({"max_drones": "1"})
        else:
            try:
                int(inst["max_drones"])
            except ValueError:
                raise ParsingError(
                    f"invalid hub capacity for {inst['id']}: "
                    f"{inst['max_drones']}"
                )
        return inst

    def parse_edge(self, line: str, element: str) -> dict[str, str]:
        if element not in ("start_hub", "end_hub", "hub", "connection"):
            raise ParsingError(f"invalid line: {element}: {line}")
        line.strip()
        inst: dict[str, str] = {}
        metadata = line.split(' ')
        if len(metadata) < 1:
            raise ParsingError(f"invalid line: {element}: {line}")
        inst.update({"id": metadata[0]})
        hubs = metadata[1].split('-')
        if len(hubs) !=  2:
            raise ParsingError(f"invalid connection: {metadata[1]}")
        inst.update({"hub1": hubs[0]})
        inst.update({"hub2": hubs[1]})
        attr: list[list[str]] = []
        for data in metadata[1:]:
            attr.append(data.lstrip('[').rstrip(']').split('='))
        for att in attr:
            if att[0] != "max_capacity_link":
                continue
            inst.update({att[0]: att[1]})
        if not inst.get("max_capacity_link"):
            inst.update({"max_capacity_link": "1"})
        else:
            try:
                int(inst["max_capacity_link"])
            except ValueError:
                raise ParsingError(
                    f"invalid connection capacity for {inst['id']}: "
                    f"{inst['max_capacity_link']}"
                )
        return inst