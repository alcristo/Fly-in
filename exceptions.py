class ParsingError(Exception):
    """Map file has incorrect structure"""
    def __init__(self, message: str) -> None:
        super().__init__(message)


class NodeError(ParsingError):
    """Hub has incorrect structure"""
    def __init__(self, message: str) -> None:
        super().__init__(message)


class EdgeError(ParsingError):
    """Connection has incorrect structure"""
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MapError(ParsingError):
    """Map issue while being constructed or solved"""
    def __init__(self, message: str) -> None:
        super().__init__(message)
