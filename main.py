"""Entry point.

Maze / Pac-Man style demo where each algorithm has a clear role:
  * DFS      -> maze generation (recursive backtracking)
  * BFS      -> red enemy chases via unweighted shortest path
  * Dijkstra -> blue enemy chases via weighted shortest path
                (avoids mud tiles, so it's smarter in practice)

Controls:
  Arrow keys / WASD  - move
  P                  - pause / resume
  D                  - toggle AI path visualization
  R                  - restart level
  Esc                - quit
"""
import sys
import pygame

from settings import WIDTH, HEIGHT, FPS
from renderer import Renderer
from game import Game


def run():
    pygame.init()
    pygame.display.set_caption("Maze Chase — DFS · BFS · Dijkstra")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    renderer = Renderer(screen)
    game = Game(renderer)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False
            else:
                game.handle_event(ev)

        game.update(dt)
        renderer.draw_frame(game)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    run()