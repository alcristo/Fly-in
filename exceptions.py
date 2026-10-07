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
