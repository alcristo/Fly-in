import pygame
from map import Map
from typing import Callable
from math import atan2, pi


"""
To draw the graph: first, draw the connections, then draw the hubs.
Plan:
    - Connections: get the hubs coordinates.
    - Hubs: coordinates.
    - Scale: Relatively small hubs, kind of long connections.
"""


def rainbow() -> Callable[[float], pygame.Color]:
    """Rotate color hue if hub color is 'rainbow'"""
    h = .0

    def rotate(a: float) -> pygame.Color:
        nonlocal h
        h += a
        h %= 360
        color = pygame.Color(0, 0, 0)
        color.hsva = (h, 100., 100., 100.)
        return color
    return rotate


class GraphicDrone:
    """Class for storing the drone that will be rendered by Pygame"""
    def __init__(
        self,
        path: str,
        orders: list[str],
        start: tuple[float, float]
    ) -> None:
        """
        Initialize a GraphicDrone class.

        Arguments:
            path: the path to the drone sprite (faces right).
            orders: list of mmovements.
            start: start hub coordinates.
        """
        self.orig_sprite = pygame.image.load(path)
        self.base_sprite = pygame.transform.smoothscale(
            self.orig_sprite, (100, 100)
        )
        self.rot_sprite = self.base_sprite
        self.steps = orders
        self.position = start
        self.rotation: float = 0
        self.fro = start
        self.to = start
        self.progress = .0
        self.duration = 1.
        self.moving = False
        self.turn = 0
        self.action_end_turn = 0
        self.move_duration_turns = 0

    def point_square(self, dx: float, dy: float) -> None:
        """
        Face up, down, left or right depending on `dx` and `dy`

        Raises:
            ArithmeticError: if either `dx` or `dy` are not zero.
        """
        if dx == 0 and dy == 0:
            raise ArithmeticError(
                "invalid coordinates for square rotation: "
                f"({dx},{dy})"
            )
        elif dx != 0 and dy != 0:
            raise ArithmeticError(
                "invalid coordinates for square rotation: "
                f"({dx},{dy})"
            )
        if dx == 0:
            if dy > 0:
                self.rot_sprite = pygame.transform.rotate(
                    self.base_sprite, 90
                )
                self.rotation = 90
            else:
                self.rot_sprite = pygame.transform.rotate(
                    self.base_sprite, 270
                )
                self.rotation = 270
        else:
            if dx > 0:
                self.rot_sprite = self.orig_sprite
                self.rotation = 0
            else:
                self.rot_sprite = pygame.transform.rotate(
                    self.base_sprite, 180
                )
                self.rotation = 180

    def point_to(self, to: tuple[float, float]) -> None:
        """Make the drone face to `to` logical position"""
        dx = to[0] - self.position[0]
        dy = to[1] - self.position[1]
        if dx == 0 and dy == 0:
            return
        angle = atan2(dy, dx) * 180 / pi
        if (dx == 0 or dy == 0):
            return self.point_square(dx, dy)
        self.rot_sprite = pygame.transform.rotate(self.base_sprite, angle)
        self.rotation = angle % 360

    def start_move(
        self,
        fro: tuple[float, float],
        to: tuple[float, float],
        duration: float
    ) -> None:
        """
        Start a drone translation.

        Arguments:
            fro: the initial logical position.
            to: the ending logical position.
        """
        self.fro = fro
        self.to = to
        self.progress = 0
        self.duration = duration
        self.point_to(to)
        self.moving = True

    def update_move(self, dt: float) -> None:
        """Make the drone move for a `dt` amount of time"""
        if not self.moving:
            return
        self.progress = min(1., self.progress + dt / self.duration)
        t = self.progress
        x = self.fro[0] * (1 - t) + self.to[0] * t
        y = self.fro[1] * (1 - t) + self.to[1] * t
        self.position = (x, y)
        if self.progress >= 1:
            self.moving = False
            self.position = self.to


class Scene:
    """Scene class for rendering the graph and drones."""
    def __init__(
            self,
            screen: pygame.surface.Surface,
            w: int,
            h: int,
            level: Map,
            solution: dict[int, list[str]]
    ) -> None:
        """
        Initialize a `Scene` class

        Arguments:
            screen: the surface where the graph will be rendered.
            w: the width.
            h: the height.
            level: the MAPF problem.
            solution: the solution to the `level`.
        """
        self.surface = screen
        self.map: Map = level
        self.zerozero: tuple[float, float] = (w // 16, h // 2)
        self.cam_x: float = 0
        self.cam_y: float = 0
        self.zoom: float = 1.0
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.last_mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        self.world_x: float = self.mouse_x / self.zoom + self.cam_x
        self.world_y: float = self.mouse_y / self.zoom + self.cam_y
        self.drag: bool = False
        self.drones: list[GraphicDrone] = [
            GraphicDrone(
                "graphics/drone1.png",
                solution[i + 1],
                self.map.start_hub.position
            ) for i in range(self.map.drones)
        ]
        self.turn: int = 0
        self._rainbow = rainbow()

    def _draw_drones(self, scale: float) -> None:
        """Render the drones"""
        if self.turn >= len(self.drones[0].steps):
            self.turn = len(self.drones[0].steps) - 1
        for i in range(len(self.drones)):
            drone = self.drones[i]
            if drone.steps[self.turn]:
                if '→' in drone.steps[self.turn]:
                    to = drone.steps[self.turn].split('→')[1]
                else:
                    to = drone.steps[self.turn]
                drone.point_to(self.map.hub(to).position)
            x = drone.position[0] * scale + self.zerozero[0]
            y = -drone.position[1] * scale + self.zerozero[1]
            screen_x = (x - self.cam_x) * self.zoom
            screen_y = (y - self.cam_y) * self.zoom
            size = max(5, round(50 * self.zoom))
            sprite = pygame.transform.smoothscale(
                drone.rot_sprite,
                (
                    round(drone.rot_sprite.get_width() * size / 100),
                    round(drone.rot_sprite.get_height() * size / 100)
                )
            )
            rect = sprite.get_rect(
                center=(round(screen_x, 2), round(screen_y, 2))
            )
            self.surface.blit(sprite, rect)

    def draw_map(self, scale: float) -> None:
        """Render the graph and drones"""
        for edge in self.map.connections:
            hub1 = edge.hub1
            hub2 = edge.hub2
            ax = hub1.position[0] * scale + self.zerozero[0]
            ay = -hub1.position[1] * scale + self.zerozero[1]
            bx = hub2.position[0] * scale + self.zerozero[0]
            by = -hub2.position[1] * scale + self.zerozero[1]
            ax = (ax - self.cam_x) * self.zoom
            ay = (ay - self.cam_y) * self.zoom
            bx = (bx - self.cam_x) * self.zoom
            by = (by - self.cam_y) * self.zoom
            pygame.draw.line(
                self.surface,
                "black",
                (ax, ay),
                (bx, by),
                max(4, int(8 * self.zoom))
            )
            pygame.draw.line(
                self.surface,
                "white",
                (ax, ay),
                (bx, by),
                max(2, int(4 * self.zoom))
            )
        for hub in self.map.hubs.values():
            x = (hub.position[0] * scale + self.zerozero[0])
            y = (-hub.position[1] * scale + self.zerozero[1])
            screen_x = (x - self.cam_x) * self.zoom
            screen_y = (y - self.cam_y) * self.zoom
            radius = max(3, int(30 * self.zoom))
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
                "gold",
                (screen_x, screen_y),
                radius,
                max(2, int(4 * self.zoom))
            )
            pygame.draw.circle(
                self.surface,
                "black",
                (screen_x, screen_y),
                radius,
                max(1, int(2 * self.zoom))
            )
        self._draw_drones(scale)

    def move_drones(self, dt: float) -> None:
        """Move the drones for a `dt` amount of time"""
        if self.turn >= len(self.drones[0].steps):
            return
        for drone in self.drones:
            if drone.moving:
                drone.update_move(dt)
                if not drone.moving:
                    drone.turn += 1
        for drone in self.drones:
            if drone.turn != self.turn:
                continue
            if self.turn < drone.action_end_turn:
                continue
            order = drone.steps[self.turn]
            duration = 1
            if not order or drone.position == self.map.goal_hub.position:
                drone.turn = self.turn + 1
                drone.action_end_turn = self.turn + 1
                continue
            drone.move_duration_turns = 1
            if drone.moving:
                continue
            if '→' in order:
                fro_id, to_id = order.split('→')
                duration *= 2
                drone.move_duration_turns *= 2
                drone.turn += 1
            else:
                to_id = order
                i = self.turn - 1
                while i >= 0 and not drone.steps[i]:
                    i -= 1
                if i < 0:
                    fro_id = self.map.start_hub.id
                elif '→' in drone.steps[i]:
                    fro_id = drone.steps[i].split('→')[1]
                else:
                    fro_id = drone.steps[i]
            fro = self.map.hub(fro_id)
            to = self.map.hub(to_id)
            drone.start_move(fro.position, to.position, duration)
            drone.move_duration_turns = duration
        done = all(
            drone.turn > self.turn
            or (
                not drone.moving
                and drone.action_end_turn <= self.turn
            ) for drone in self.drones
        )
        if done:
            self.turn += 1

    def restart(self) -> None:
        """Set the drones to their initial state"""
        for drone in self.drones:
            drone.position = self.map.start_hub.position
            drone.rotation = 0
            drone.moving = False
            drone.turn = 0
            drone.progress = 0
            drone.fro = self.map.start_hub.position
            drone.to = self.map.start_hub.position
            drone.action_end_turn = 0
            drone.move_duration_turns = 0
        self.turn = 0


def draw_map(
    level: Map,
    solution: dict[int, list[str]],
    scale: int,
    resolution: tuple[int, int] = (640, 480)
) -> None:
    """
    Render the Pygame window with the MAPF solution animation.

    Arguments:
        level: the MAPF probem.
        solution: the solution to `level`.
        scale: how big will the hubs, connections and drone sprites.
        resolution: the screen resolution.
    """

    # Initialize the Pygame window
    pygame.init()
    pygame.display.set_caption("Fly-in")
    drone_surface = pygame.image.load("graphics/drone1.png")
    pygame.display.set_icon(drone_surface)
    screen = pygame.display.set_mode(resolution)
    w, h = resolution

    # Initialize the scene and the buttons images and rectangles
    scene = Scene(screen, w, h, level, solution)
    play_img = pygame.image.load("graphics/play.png")
    pause_img = pygame.image.load("graphics/pause.png")
    replay_img = pygame.image.load("graphics/replay.png")
    ff_img = pygame.image.load("graphics/fast_forward.png")
    sd_img = pygame.image.load("graphics/slow_down.png")
    button_size = play_img.get_size()
    x_img = screen.get_size()[0] - button_size[0]
    y_img = screen.get_size()[1] - button_size[1]
    ff = pygame.Rect(x_img, y_img, button_size[0], button_size[1])
    play = pygame.Rect(
        x_img - button_size[0] - 1,
        y_img, button_size[0], button_size[1]
    )
    replay = pygame.Rect(
        x_img - 2 * button_size[0] - 1,
        y_img, button_size[0], button_size[1]
    )
    sd = pygame.Rect(
        x_img - 3 * button_size[0] - 1,
        y_img, button_size[0], button_size[1]
    )

    # Time and text
    t = 2.
    t_rect = pygame.Rect(w - 150, 0, 150, 40)
    text_rect = pygame.Rect(w - 130, 10, 130, 20)
    font = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()
    pause = True
    running = True
    fps = 60

    # Event loop
    while running:
        for event in pygame.event.get():
            # Close the window
            if event.type == pygame.QUIT:
                running = False
            # Zoom
            elif event.type == pygame.MOUSEWHEEL:
                scene.mouse_x, scene.mouse_y = pygame.mouse.get_pos()
                scene.world_x = scene.cam_x + scene.mouse_x / scene.zoom
                scene.world_y = scene.cam_y + scene.mouse_y / scene.zoom
                if event.y > 0:
                    scene.zoom *= 1.1
                else:
                    scene.zoom /= 1.1
                scene.zoom = max(.2, min(scene.zoom, 5.))
                scene.cam_x = scene.world_x - scene.mouse_x / scene.zoom
                scene.cam_y = scene.world_y - scene.mouse_y / scene.zoom
            # Click
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if play.collidepoint(event.pos):
                        pause = not pause
                    elif replay.collidepoint(event.pos):
                        if not pause:
                            pause = not pause
                        scene.restart()
                    elif ff.collidepoint(event.pos):
                        t = min(8, t * 2)
                    elif sd.collidepoint(event.pos):
                        t = max(.5, t / 2)
                    else:
                        scene.drag = True
                        scene.last_mouse_pos = pygame.mouse.get_pos()
            # Release click
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    scene.drag = False
            # Pan while clicking
            elif event.type == pygame.MOUSEMOTION:
                if scene.drag:
                    scene.mouse_x, scene.mouse_y = pygame.mouse.get_pos()
                    dx = scene.last_mouse_pos[0] - scene.mouse_x
                    dy = scene.last_mouse_pos[1] - scene.mouse_y
                    scene.cam_x += dx / scene.zoom
                    scene.cam_y += dy / scene.zoom
                    scene.last_mouse_pos = (scene.mouse_x, scene.mouse_y)
        # Render the scene
        screen.fill("lightgray")
        if not pause:
            scene.move_drones(t / fps)
        scene.draw_map(scale)
        # Render the turn counter
        pygame.draw.rect(screen, "black", t_rect)
        text = font.render(f"Turns: {scene.turn + 1}", True, "white")
        # Render the buttons
        if pause is True:
            screen.blit(play_img, (x_img - button_size[0], y_img))
        else:
            screen.blit(pause_img, (x_img - button_size[0], y_img))
        screen.blit(replay_img, (x_img - 2 * button_size[0], y_img))
        screen.blit(ff_img, (x_img, y_img))
        screen.blit(sd_img, (x_img - 3 * button_size[0], y_img))
        screen.blit(text, text_rect)
        pygame.display.update()
        clock.tick(fps)
    pygame.quit()
