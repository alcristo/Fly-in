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
        x: float = (coords[0] - self.cam_x) * self.lens * scale
        y: float = (coords[1] - self.cam_y) * self.lens * scale
        return (x, y)

    def _get_hub_position(self, hub: Hub, scale: int) -> tuple[float, float]:
        x = (self.zerozero[0] + hub.position[0] - self.cam_x) * self.lens * scale
        y = (self.zerozero[1] + hub.position[1] - self.cam_y) * self.lens * scale
        return (x, y)

    def _get_hub_radius(self, radius: int, scale: int) -> int:
        return 5 * scale

    def draw_map(self, scale: int) -> None:
        for edge in self.map.connections:
            hub1 = edge.hub1
            hub2 = edge.hub2
            pygame.draw.line(self.surface, "black", self._get_hub_position(hub1, scale), self._get_hub_position(hub2, scale), 4)
            pygame.draw.line(self.surface, "white", self._get_hub_position(hub1, scale), self._get_hub_position(hub2, scale), 2)
        for hub in self.map.hubs.values():
            if hub.color.lower() == "rainbow":
                pygame.draw.circle(self.surface, self._rainbow(2), self._get_hub_position(hub, scale), 5 * scale)
            else:
                pygame.draw.circle(self.surface, hub.color.lower(), self._get_hub_position(hub, scale), 5 * scale)
            pygame.draw.circle(self.surface, "black", self._get_hub_position(hub, scale), 50 * scale, 2)

    def pan(self):
        if self.drag:
            self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
            dx = self.mouse_x - self.last_mouse_pos[0]
            dy = self.mouse_y - self.last_mouse_pos[1]
            self.cam_x = dx / self.lens
            self.cam_y = dy / self.lens
            self.last_mouse_pos = (self.mouse_x, self.mouse_y)

    def zoom(self, event: pygame.event.Event):
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.world_x = self.mouse_x / self.lens + self.cam_x
        self.world_y = self.mouse_y / self.lens + self.cam_y
        if event.y > 0:
            self.lens *= 1.1
        else:
            self.lens /= 1.1
        self.lens = max(.2, min(self.lens, 5.))
        self.cam_x = self.world_x - self.mouse_x / self.lens
        self.cam_y = self.world_y - self.mouse_y / self.lens


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
                scene.drag = True
                scene.last_mouse_pos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONUP:
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
    my_font = pygame.font.Font(None, 64)
    running = True
    # hub = pygame.image.load("graphics/hub.png")
    ground = pygame.Surface((800,600))
    ground.fill("purple")
    next_color = rainbow()
    # color = pygame.Color()
    text = my_font.render(chr(9773), False, "yellow")
    # hub.fill("red")

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close the window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with color to wipe anything from last frame
        screen.fill("black")

        # RENDER YOUR GAME HERE
        # screen.blit(ground, (0,0))
        # pygame.draw.line(screen, "black", (0,0), (800,600), 3)
        # pygame.draw.circle(screen, "red", (400,300), 100)
        pygame.draw.circle(screen, next_color(2), (400, 300), 100)
        # screen.blit(hub, (300,250))
        # screen.blit(text, (350,280))

        # flip() the display to put your work on screen
        pygame.display.flip()  # pygame.display.update()

        clock.tick(30)  # limits FPS to 30

    pygame.quit()

"""
    pygame.init()

    WIDTH, HEIGHT = 1000, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    # Graph coordinates -- these never change.
    nodes = {
        "A": (100, 100),
        "B": (400, 150),
        "C": (250, 400),
        "D": (600, 350),
    }
    
    edges = [
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("C", "D"),
    ]
    
    zoom = 1.0
    camera_x = 0
    camera_y = 0
    
    running = True

    mouse_x, mouse_y = pygame.mouse.get_pos()

# World coordinate currently underneath mouse
    world_x = mouse_x / zoom + camera_x
    world_y = mouse_y / zoom + camera_y
    
    # Change zoom
    zoom *= 1.1
    
    # Adjust camera so the same world position stays under mouse
    camera_x = world_x - mouse_x / zoom
    camera_y = world_y - mouse_y / zoom

    dragging = False
    last_mouse = None
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
            # Mouse wheel = zoom
            elif event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
            
                # Position in the graph under the cursor
                world_x = mouse_x / zoom + camera_x
                world_y = mouse_y / zoom + camera_y
            
                if event.y > 0:
                    zoom *= 1.1
                else:
                    zoom /= 1.1
            
                zoom = max(0.2, min(zoom, 5.0))
            
                # Keep that graph position under the cursor
                camera_x = world_x - mouse_x / zoom
                camera_y = world_y - mouse_y / zoom

            if event.type == pygame.MOUSEBUTTONDOWN:
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

        screen.fill((30, 30, 30))
    
        # Draw edges
        for a, b in edges:
            ax, ay = nodes[a]
            bx, by = nodes[b]
    
            ax = (ax - camera_x) * zoom
            ay = (ay - camera_y) * zoom
    
            bx = (bx - camera_x) * zoom
            by = (by - camera_y) * zoom
    
            pygame.draw.line(
                screen,
                (180, 180, 180),
                (ax, ay),
                (bx, by),
                max(1, int(3 * zoom))
            )
    
        # Draw nodes
        for name, (x, y) in nodes.items():
            screen_x = (x - camera_x) * zoom
            screen_y = (y - camera_y) * zoom
    
            radius = max(3, int(15 * zoom))
    
            pygame.draw.circle(
                screen,
                "maroon",
                (int(screen_x), int(screen_y)),
                radius
            )
    
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
"""


if __name__ == "__main__":
    main()