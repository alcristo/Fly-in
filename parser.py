from models import MapData, Hub, Connection, Zone
from exceptions import ParsingError, NodeError, EdgeError


"""
If keeps being hard, either:
    - Find a parser library
    - Convert to JSON
    - Use tqdm for loading bar
"""


class Parser:
    """Parser class for map parsing from .txt files"""

    def _init_hub(self, node_dict: dict[str, str]) -> Hub:
        """
        Initialize zone in the map data

        Arguments:
            node_dict: A dictionary containing the zone information

        Returns:
            new_hub: The parsed hub

        Raises:
            NodeError: one of the keys is missing (unikely) or
                Pydantic fails to validate the zone
        """
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
            raise NodeError(f"invalid hub: {node_dict}")
        return new_hub

    def _hub_in_list(self, name: str, hubs: dict[str, Hub]) -> bool:
        """
        Checks if a hub is in the dictionary

        Arguments:
            name: the hub name
            hubs: a dictionary containing the hubs with their names as keys

        Returns:
            Boolean: Whether the hub is in the dictionary
        """
        keys = hubs.keys()
        for key in keys:
            if key == name:
                return True
        return False

    def _get_hub(self, name: str, hubs: dict[str, Hub]) -> Hub:
        """
        Return name labeled hub from hubs dictionary

        Arguments:
            name: the hub name
            hubs: a dictionary containing the hubs with their names as keys

        Returns:
            hub: the hub labeled name

        Raises:
            NodeError: if hub not in hubs
        """
        for key, hub in hubs.items():
            if key == name:
                return hub
        raise NodeError(f"{name} is not a hub")

    def _init_connection(
        self, edge_dict: dict[str, str], hubs: dict[str, Hub]
    ) -> Connection:
        """
        Initialize connection in the map data

        Arguments:
            edge_dict: A dictionary containing the link information
            hubs: a dictionary containing all zones with their names as keys

        Returns:
            new_connection: The parsed connection

        Raises:
            KeyError: if one of the keys is missing (unikely)
            ValueError: If Pydantic fails to validate the zone
            NodeError: if any of the hubs in the connection not in hubs
        """
        try:
            hub1 = self._get_hub(edge_dict["hub1"], hubs)
            hub2 = self._get_hub(edge_dict["hub2"], hubs)
            new_connection = Connection(
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
        """
        Parse a text file into a map

        Arguments:
            path: the path to the text file

        Returns:
            map_data: a map data with all the information

        Raises:
            ParsingError: Map file has incorrect structure
            NodeError: Hub has incorrect structure
            EdgeError: Connection has incorrect structure
        """

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
                raise ParsingError(f"invalid line: {''.join(line)}")
            if line[0] == "nb_drones":
                try:
                    nb_drones = int(line[1])
                except ValueError:
                    raise ParsingError(f"invalid number of drones: {line[1]}")
            elif line[0] == "start_hub":
                if len(start_node.keys()):
                    raise ParsingError("more than one start hub in map")
                start_node = self.parse_zone(line[1], "start_hub", nb_drones)
            elif line[0] == "end_hub":
                if len(end_node.keys()):
                    raise ParsingError("more than one end hub in map")
                end_node = self.parse_zone(line[1], "end_hub", nb_drones)
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
        map_data = MapData(
            nb_drones=nb_drones,
            start_hub=start_hub,
            end_hub=end_hub,
            hubs=hubs,
            connections=connections
        )
        return map_data

    def parse_zone(
        self,
        line: str,
        element: str,
        n: int = 1
    ) -> dict[str, str]:
        """
        Parse a zone

        Arguments:
            line: the hub line containing the name, coordinates and metadata.
            element: can he 'hub', 'start_hub' or 'end_hub'.

        Keyword arguments:
            n: Number of drones that may hold the hub (default 1).
            Only for start and end hubs.

        Returns:
            inst: an instance of the hub as a dictionary

        Raises:
            ParsingError: hub data is invalid
        """
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
        if len(metadata) > 3:
            attr: list[list[str]] = []
            for data in metadata[3:]:
                attribute = data.lstrip('[').rstrip(']').split('=')
                if len(attribute) != 2:
                    raise ParsingError(f"invalid attribute: {attribute}")
                attr.append(attribute)
            for att in attr:
                if att[0] not in ("color", "zone", "max_drones"):
                    continue
                elif att[0] == "max_drones":
                    if element == "hub":
                        inst.update({"max_drones": att[1]})
                    else:
                        inst.update({"max_drones": str(n)})
                else:
                    inst.update({att[0]: att[1]})
        if not inst.get("color"):
            inst.update({"color": "white"})
        if not inst.get("zone"):
            inst.update({"zone": "normal"})
        else:
            if element == "hub":
                try:
                    assert inst["zone"] in (
                        "normal", "priority", "restricted", "blocked"
                    )
                except AssertionError:
                    raise ParsingError(
                        f"invalid zone type for {inst['id']}"
                        f": {inst['zone']}"
                    )
            else:
                inst["zone"] = "normal"
        if not inst.get("max_drones"):
            if element == "hub":
                inst.update({"max_drones": "1"})
            else:
                inst.update({"max_drones": str(n)})
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
        """
        Parse a connection

        Arguments:
            line: the link line containing the name, coordinates and metadata.
            element: must be 'connection'.

        Keyword arguments:
            n: Number of drones that may hold the hub (default 1).
            Only for start and end hubs.

        Returns:
            inst: An instance of the connection as a dictionary

        Raises:
            ParsingError: Connection data is invalid
        """
        if element != "connection":
            raise ParsingError(f"invalid line: {element}: {line}")
        line.strip()
        inst: dict[str, str] = {}
        metadata = line.split(' ')
        if len(metadata) < 1:
            raise ParsingError(f"invalid line: {element}: {line}")
        while "" in metadata:
            metadata.remove("")
        # inst.update({"id": metadata[0]})
        hubs = metadata[0].split('-')
        if len(hubs) != 2:
            raise ParsingError(f"invalid connection: {metadata[0]}")
        inst.update({"hub1": hubs[0]})
        inst.update({"hub2": hubs[1]})
        if len(metadata) > 1:
            attr: list[list[str]] = []
            for data in metadata[1:]:
                attribute = data.lstrip('[').rstrip(']').split('=')
                if len(attribute) != 2:
                    raise ParsingError(f"invalid attribute: {attribute}")
                attr.append(attribute)
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
                    "invalid connection capacity for"
                    f"{inst['hub1']}-{inst['hub2']}: "
                    f"{inst['max_link_capacity']}"
                )
        return inst
