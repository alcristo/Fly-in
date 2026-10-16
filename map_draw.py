import pygame
from map import Map
from typing import Callable
from math import atan2, pi, sin, cos, sqrt


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


class GraphicDrone:
    def __init__(
        self,
        path: str,
        orders: list[str],
        start: tuple[float, float]
    ) -> None:
        self.orig_sprite = pygame.image.load(path)
        self.rot_sprite = pygame.image.load(path)
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
                    self.orig_sprite, 90
                )
                self.rotation = 90
            else:
                self.rot_sprite = pygame.transform.rotate(
                    self.orig_sprite, 270
                )
                self.rotation = 270
        else:
            if dx > 0:
                self.rot_sprite = self.orig_sprite
                self.rotation = 0
            else:
                self.rot_sprite = pygame.transform.rotate(
                    self.orig_sprite, 180
                )
                self.rotation = 180

    def point_to(self, to: tuple[float, float]) -> None:
        dx = to[0] - self.position[0]
        dy = to[1] - self.position[1]
        if dx == 0 and dy == 0:
            return
        angle = atan2(dy, dx) * 180 / pi
        if (dx == 0 or dy == 0):
            return self.point_square(dx, dy)
        self.rot_sprite = pygame.transform.rotate(self.orig_sprite, angle)
        self.rotation = angle % 360

    def start_move(
        self,
        fro: tuple[float, float],
        to: tuple[float, float],
        duration: float
    ) -> None:
        self.fro = fro
        self.to = to
        self.progress = 0
        self.duration = duration
        self.point_to(to)
        self.moving = True

    def update_move(self, dt: float) -> None:
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
    def __init__(
            self,
            screen: pygame.Surface,
            w: int,
            h: int,
            level: Map,
            solution: dict[int, list[str]]
    ) -> None:
        self.surface = screen
        self.map: Map = level
        self.zerozero: tuple[float, float] = (w // 16, h // 2)
        self.cam_x: float = 0
        self.cam_y: float = 0
        self.lens: float = 1.0
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.last_mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        self.world_x: float = self.mouse_x / self.lens + self.cam_x
        self.world_y: float = self.mouse_y / self.lens + self.cam_y
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

    def draw_drones(self, scale: float) -> None:
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
            screen_x = (x - self.cam_x) * self.lens
            screen_y = (y - self.cam_y) * self.lens
            size = max(5, 50 * self.lens)
            sprite = pygame.transform.smoothscale(
                drone.rot_sprite, (size, size)
            )
            rect = sprite.get_rect(
                center=(round(screen_x, 2), round(screen_y, 2))
            )
            self.surface.blit(sprite, rect)

    def draw_map(self, scale: float) -> None:
        for edge in self.map.connections:
            hub1 = edge.hub1
            hub2 = edge.hub2
            ax = hub1.position[0] * scale + self.zerozero[0]
            ay = -hub1.position[1] * scale + self.zerozero[1]
            bx = hub2.position[0] * scale + self.zerozero[0]
            by = -hub2.position[1] * scale + self.zerozero[1]
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
            y = (-hub.position[1] * scale + self.zerozero[1])
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
                "gold",
                (screen_x, screen_y),
                radius,
                max(2, int(4 * self.lens))
            )
            pygame.draw.circle(
                self.surface,
                "black",
                (screen_x, screen_y),
                radius,
                max(1, int(2 * self.lens))
            )
            self.draw_drones(scale)

    def move_drones(self, dt: float):
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
                if self.turn == 0 or not drone.steps[self.turn - 1]:
                    i = self.turn - 1
                    while i > 0 and not drone.steps[i]:
                        i -= 1
                    if i <= 0:
                        fro_id = self.map.start_hub.id
                    else:
                        fro_id = drone.steps[i]
                elif '→' in drone.steps[self.turn - 1]:
                    fro_id = drone.steps[self.turn - 1].split('→')[1]
                else:
                    fro_id = drone.steps[self.turn - 1]
            fro = self.map.hub(fro_id)
            to = self.map.hub(to_id)
            print(f"{fro_id}-{to_id}")
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

    def restart(self):
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


def draw_map(level: Map, solution: dict[int, list[str]], scale: int):
    pygame.init()
    pygame.display.set_caption("Fly-in")
    drone_surface = pygame.image.load("graphics/drone1.png")
    pygame.display.set_icon(drone_surface)
    screen = pygame.display.set_mode((1200, 800))
    scene = Scene(screen, 1200, 800, level, solution)
    play_img = pygame.image.load("graphics/play.png")
    pause_img = pygame.image.load("graphics/pause.png")
    replay_img = pygame.image.load("graphics/replay.png")
    button_size = play_img.get_size()
    x_img = screen.get_size()[0] - button_size[0]
    y_img = screen.get_size()[1] - button_size[1]
    play = pygame.Rect(x_img, y_img, button_size[0], button_size[1])
    replay = pygame.Rect(
        x_img - button_size[0] - 1,
        y_img, button_size[0], button_size[1]
    )
    clock = pygame.time.Clock()
    pause = True
    running = True
    fps = 60
    v = 3
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                scene.mouse_x, scene.mouse_y = pygame.mouse.get_pos()
                scene.world_x = scene.cam_x + scene.mouse_x / scene.lens
                scene.world_y = scene.cam_y + scene.mouse_y / scene.lens
                if event.y > 0:
                    scene.lens *= 1.1
                else:
                    scene.lens /= 1.1
                scene.lens = max(.2, min(scene.lens, 5.))
                scene.cam_x = scene.world_x - scene.mouse_x / scene.lens
                scene.cam_y = scene.world_y - scene.mouse_y / scene.lens
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if play.collidepoint(event.pos):
                        pause = not pause
                    elif replay.collidepoint(event.pos):
                        if not pause:
                            pause = not pause
                        scene.restart()
                    else:
                        scene.drag = True
                        scene.last_mouse_pos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    scene.drag = False
            elif event.type == pygame.MOUSEMOTION:
                if scene.drag:
                    scene.mouse_x, scene.mouse_y = pygame.mouse.get_pos()
                    dx = scene.last_mouse_pos[0] - scene.mouse_x
                    dy = scene.last_mouse_pos[1] - scene.mouse_y
                    scene.cam_x += dx / scene.lens
                    scene.cam_y += dy / scene.lens
                    scene.last_mouse_pos = (scene.mouse_x, scene.mouse_y)
        screen.fill("lightgray")
        if not pause:
            scene.move_drones(2 / fps)
        scene.draw_map(scale)
        if pause is True:
            screen.blit(play_img, (x_img, y_img))
        else:
            screen.blit(pause_img, (x_img, y_img))
        screen.blit(replay_img, (x_img - button_size[0], y_img))
        pygame.display.update()
        clock.tick(fps)
    pygame.quit()
