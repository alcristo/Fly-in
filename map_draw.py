import pygame
from map import Map
from models import Hub
from typing import Callable


"""
To draw the graph: first, draw the connections, then draw the hubs.
Plan:
    - Connections: get the hubs coordinates.
    - Hubs: coordinates.
    - Scale: Relatively small hubs, kind of long connections.
"""


def rainbow() -> Callable[[float], pygame.Color]:
    h = .0

    def rotate(a: float) -> pygame.Color:
        nonlocal h
        h += a
        h %= 360
        color = pygame.Color(0, 0, 0)
        color.hsva = (h, 100., 100., 100.)
        return color
    return rotate


class Scene:  # (pygame.Surface):
    def __init__(self, screen: pygame.Surface, w: int, h: int, level: Map) -> None:
        # super().__init__((w, h))
        self.surface = screen
        self.map: Map = level
        self.zerozero: tuple[float, float] = (w // 8, h // 2)
        self.cam_x: float = 0
        self.cam_y: float = 0
        self.lens: float = 1.0
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.last_mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        self.world_x: float = self.mouse_x / self.lens + self.cam_x
        self.world_y: float = self.mouse_y / self.lens + self.cam_y
        self.drag: bool = False
        self._rainbow = rainbow()

    def _scale(self, coords: tuple[int, int], scale: int) -> tuple[float, float]:
        x: float = (coords[0] * scale - self.cam_x) * self.lens
        y: float = (coords[1] * scale - self.cam_y) * self.lens
        return (x, y)

    def _get_hub_position(self, hub: Hub, scale: int) -> tuple[float, float]:
        # x = (self.zerozero[0] + hub.position[0] * scale - self.cam_x) * self.lens
        # y = (self.zerozero[1] + hub.position[1] * scale - self.cam_y) * self.lens
        x = self.mouse_x + (self.zerozero[0] + hub.position[0] * scale - self.mouse_x) * self.lens
        y = self.mouse_y + (self.zerozero[1] + hub.position[1] * scale - self.mouse_y) * self.lens
        return (x, y)

    def _get_hub_radius(self, radius: int, scale: int) -> int:
        return 5 * scale

    def draw_map(self, scale: float) -> None:
        for edge in self.map.connections:
            hub1 = edge.hub1
            hub2 = edge.hub2
            ax = (hub1.position[0] * scale + self.zerozero[0])
            ay = (hub1.position[1] * scale + self.zerozero[1])
            bx = (hub2.position[0] * scale + self.zerozero[0])
            by = (hub2.position[1] * scale + self.zerozero[1])
            ax = (ax - self.cam_x) * self.lens
            ay = (ay - self.cam_y) * self.lens
            bx = (bx - self.cam_x) * self.lens
            by = (by - self.cam_y) * self.lens
            pygame.draw.line(
                self.surface,
                "black",
                (ax, ay),
                (bx, by),
                max(4, int(8 * self.lens))
            )
            pygame.draw.line(
                self.surface,
                "white",
                (ax, ay),
                (bx, by),
                max(2, int(4 * self.lens))
            )
        for hub in self.map.hubs.values():
            x = (hub.position[0] * scale + self.zerozero[0])
            y = (hub.position[1] * scale + self.zerozero[1])
            screen_x = (x - self.cam_x) * self.lens
            screen_y = (y - self.cam_y) * self.lens
            radius = max(3, int(30 * self.lens))
            if hub.color.lower() == "rainbow":
                pygame.draw.circle(
                    self.surface,
                    self._rainbow(2),
                    (screen_x, screen_y),
                    radius
                )
            else:
                pygame.draw.circle(
                    self.surface,
                    hub.color.lower(),
                    (screen_x, screen_y),
                    radius
                )
            pygame.draw.circle(
                self.surface,
                "black",
                (screen_x, screen_y),
                radius,
                max(2, int(4 * self.lens))
            )

    def pan(self):
        if self.drag:
            self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
            dx = self.mouse_x + self.last_mouse_pos[0]
            dy = self.mouse_y + self.last_mouse_pos[1]
            self.cam_x = dx / self.lens
            self.cam_y = dy / self.lens
            self.last_mouse_pos = (self.mouse_x, self.mouse_y)

    def zoom(self, event: pygame.event.Event):
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.world_x = self.mouse_x / self.lens - self.cam_x
        self.world_y = self.mouse_y / self.lens - self.cam_y
        if event.y > 0:
            self.lens *= 1.1
        else:
            self.lens /= 1.1
        self.lens = max(.2, min(self.lens, 5.))
        self.cam_x = self.world_x + self.mouse_x / self.lens
        self.cam_y = self.world_y + self.mouse_y / self.lens


def draw_map(level: Map, scale: int):
    pygame.init()
    pygame.display.set_caption("Fly-in")
    screen = pygame.display.set_mode((1500, 1000))
    scene = Scene(screen, 1500, 1000, level)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                scene.zoom(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    scene.drag = True
                    scene.last_mouse_pos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    scene.drag = False
            elif event.type == pygame.MOUSEMOTION:
                scene.pan()
        screen.fill("purple")
        scene.draw_map(scale)
        pygame.display.update()
        clock.tick(60)
    pygame.quit()


def main() -> None:
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Fly-in")
    clock = pygame.time.Clock()
    # my_font = pygame.font.Font(None, 64)
    running = True
    # hub = pygame.image.load("graphics/hub.png")
    # ground = pygame.Surface((800,600))
    # ground.fill("purple")
    next_color = rainbow()
    # color = pygame.Color()
    #  text = my_font.render(chr(9773), False, "yellow")
    # hub.fill("red")

    nodes = {
        "A": (200, 300),
        "B": (600, 300)
    }
    edges = [("A", "B")]
    mouse_x, mouse_y = pygame.mouse.get_pos()
    zoom = 1.
    camera_x, camera_y = 0, 0
    world_x = mouse_x / zoom + camera_x
    world_y = mouse_y / zoom + camera_y
    dragging = False
    last_mouse = None

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close the window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                world_x = mouse_x / zoom + camera_x
                world_y = mouse_y / zoom + camera_y
                if event.y > 0:
                    zoom *= 1.1
                else:
                    zoom /= 1.1
                zoom = max(.2, min(zoom, 5.))
                camera_x = world_x - mouse_x / zoom
                camera_y = world_y - mouse_y / zoom

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    last_mouse = pygame.mouse.get_pos()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    mouse_x, mouse_y = event.pos
                    dx = mouse_x - last_mouse[0]
                    dy = mouse_y - last_mouse[1]
                    camera_x -= dx / zoom
                    camera_y -= dy / zoom
                    last_mouse = (mouse_x, mouse_y)

        # fill the screen with color to wipe anything from last frame
        screen.fill("black")

        # RENDER YOUR GAME HERE
        # screen.blit(ground, (0,0))
        # pygame.draw.line(screen, "black", (0,0), (800,600), 3)
        # pygame.draw.circle(screen, "red", (400,300), 100)
        for a, b in edges:
            ax, ay = nodes[a]
            bx, by = nodes[b]
            ax = (ax - camera_x) * zoom
            ay = (ay - camera_y) * zoom
            bx = (bx - camera_x) * zoom
            by = (by - camera_y) * zoom
            pygame.draw.line(screen, "green", (ax, ay), (bx, by), max(1, int(3 * zoom)))
        for name, (x, y) in nodes.items():
            screen_x = (x - camera_x) * zoom
            screen_y = (y - camera_y) * zoom
            radius = max(5, int(50 * zoom))
            pygame.draw.circle(screen, "white", (screen_x, screen_y), radius)
        # screen.blit(hub, (300,250))
        # screen.blit(text, (350,280))

        # flip() the display to put your work on screen
        pygame.display.flip()  # pygame.display.update()

        clock.tick(60)  # limits FPS to 30

    pygame.quit()


if __name__ == "__main__":
    main()
