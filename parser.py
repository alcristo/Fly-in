from models import MapData, Hub, Connection, Zone


"""
If keeps being hard, either:
    - Find a parser library
    - Convert to JSON
    - Use tqdm for loading bar
"""


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

    def _init_hub(self, node_dict: dict[str, str]) -> Hub:
        try:
            new_hub = Hub(
                id=node_dict["id"],
                position=(int(node_dict["x"]), int(node_dict["y"])),
                color=node_dict["color"],
                zone=Zone(node_dict["zone"]),
                capacity=int(node_dict["max_drones"])
            )
        except KeyError as e:
            raise NodeError(f"missing key for hub: {e.__str__}")
        except ValueError:
            raise ParsingError(f"invalid hub: {node_dict}")
        return new_hub

    def _hub_in_list(self, name: str, hubs: dict[str, Hub]) -> bool:
        keys = hubs.keys()
        for key in keys:
            if key == name:
                return True
        return False

    def _get_hub(self, name: str, hubs: dict[str, Hub]) -> Hub:
        for key, hub in hubs.items():
            if key == name:
                return hub
        raise NodeError(f"{name} is not a hub")

    def _init_connection(
        self, edge_dict: dict[str, str], hubs: dict[str, Hub]
    ) -> Connection:
        try:
            hub1 = self._get_hub(edge_dict["hub1"], hubs)
            hub2 = self._get_hub(edge_dict["hub2"], hubs)
            new_connection = Connection(
                id=edge_dict["id"],
                hub1=hub1,
                coords1=hub1.position,
                hub2=hub2,
                coords2=hub2.position,
                capacity=int(edge_dict["max_link_capacity"])
            )
        except KeyError as e:
            raise EdgeError(f"missing key for connection: {e.__str__}")
        except ValueError:
            raise EdgeError(f"invalid connection: {edge_dict}")
        return new_connection

    def parse(self, path: str) -> MapData:

        # Open and read the file
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
        print(txt)

        # Define nodes and edges dictionaries
        nb_drones = 0
        start_node: dict[str, str] = {}
        end_node: dict[str, str] = {}
        nodes: list[dict[str, str]] = []
        edges: list[dict[str, str]] = []
        for line in valid_lines:
            if (len(line) != 2):
                raise ParsingError(f"invalid line: {line}")
            if line[0] not in (
                "nb_drones", "start_hub", "end_hub", "hub", "connection"
            ):
                raise ParsingError(f"invalid line: {line}")
            if line[0] == "nb_drones":
                try:
                    nb_drones = int(line[1])
                except ValueError:
                    raise ParsingError(f"invalid number of drones: {line[1]}")
            elif line[0] == "start_hub":
                if len(start_node.keys()):
                    raise ParsingError("more than one start hub in map")
                start_node = self.parse_zone(line[1], "start_hub")
            elif line[0] == "end_hub":
                if len(end_node.keys()):
                    raise ParsingError("more than one end hub in map")
                end_node = self.parse_zone(line[1], "end_hub")
            elif line[0] == "hub":
                nodes.append(self.parse_zone(line[1], "hub"))
            elif line[0] == "connection":
                edges.append(self.parse_edge(line[1], "connection"))
        if not start_node:
            raise NodeError("start hub not found")
        if not end_node:
            raise NodeError("goal hub not found")

        # Set the nodes to hubs and edges to connections
        start_hub = self._init_hub(start_node)
        end_hub = self._init_hub(end_node)
        hubs: dict[str, Hub] = {}
        connections: list[Connection] = []
        for node in nodes:
            if not hubs.get(node["id"]):
                hubs.update({node["id"]: self._init_hub(node)})
            else:
                raise ParsingError(f"duplicated node: {node['id']}")
        hubs.update({start_hub.id: start_hub})
        hubs.update({end_hub.id: end_hub})
        for edge in edges:
            try:
                assert self._hub_in_list(edge["hub1"], hubs)
                assert self._hub_in_list(edge["hub2"], hubs)
            except AssertionError:
                raise EdgeError(f"{edge['hub1']} or {edge['hub2']} not in map")
            connections.append(self._init_connection(edge, hubs))
        hubs.pop(start_hub.id)
        hubs.pop(end_hub.id)
        return MapData(
            nb_drones=nb_drones,
            start_hub=start_hub,
            end_hub=end_hub,
            hubs=hubs,
            connections=connections
        )

    def parse_zone(self, line: str, element: str) -> dict[str, str]:
        line.strip()
        inst: dict[str, str] = {}
        metadata = line.split(' ')
        while "" in metadata:
            metadata.remove("")
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
        if len(hubs) != 2:
            raise ParsingError(f"invalid connection: {metadata[1]}")
        inst.update({"hub1": hubs[0]})
        inst.update({"hub2": hubs[1]})
        attr: list[list[str]] = []
        for data in metadata[1:]:
            attr.append(data.lstrip('[').rstrip(']').split('='))
        for att in attr:
            if att[0] != "max_link_capacity":
                continue
            inst.update({att[0]: att[1]})
        if not inst.get("max_link_capacity"):
            inst.update({"max_link_capacity": "1"})
        else:
            try:
                int(inst["max_link_capacity"])
            except ValueError:
                raise ParsingError(
                    f"invalid connection capacity for {inst['id']}: "
                    f"{inst['max_link_capacity']}"
                )
        return inst
