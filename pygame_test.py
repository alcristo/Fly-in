import pygame


def main():
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

if __name__ == "__main__":
    main()
