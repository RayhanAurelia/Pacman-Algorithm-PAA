import math
import pygame
from settings import (
    TILE, HUD_HEIGHT, WIDTH, HEIGHT, COLS, ROWS, WALL_THICK,
    BLACK, BG_DEEP, WALL, WALL_DARK, WALL_HL,
    FLOOR, FLOOR_DOT, MUD, MUD_DARK, MUD_HL,
    PELLET, PELLET_GLOW,
    PLAYER, PLAYER_DARK, PLAYER_HL,
    ENEMY_BFS, ENEMY_BFS_HL, ENEMY_DIJK, ENEMY_DIJK_HL,
    ENEMY_EYE, ENEMY_PUPIL,
    TEXT, TEXT_DIM, HUD_BG, HUD_LINE,
    WIN_COLOR, LOSE_COLOR,
)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font_small = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_mid   = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_big   = pygame.font.SysFont("consolas", 46, bold=True)
        self.maze_w = COLS * TILE
        self.maze_h = ROWS * TILE
        self.maze_surf = pygame.Surface((self.maze_w, self.maze_h)).convert()
        self.glow_surf = pygame.Surface((self.maze_w, self.maze_h), pygame.SRCALPHA).convert_alpha()
        self.path_surf = pygame.Surface((self.maze_w, self.maze_h), pygame.SRCALPHA).convert_alpha()
        self._mud_overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA).convert_alpha()
        self._build_mud_overlay()
        self.maze_dirty = True
        self.time = 0.0

    # ---------- static textures ----------

    def _build_mud_overlay(self):
        s = self._mud_overlay
        s.fill((0, 0, 0, 0))
        # subtle splotches
        for (dx, dy, r, c) in [
            (TILE * 0.25, TILE * 0.30, TILE * 0.18, (*MUD_DARK, 130)),
            (TILE * 0.70, TILE * 0.55, TILE * 0.16, (*MUD_DARK, 110)),
            (TILE * 0.55, TILE * 0.80, TILE * 0.10, (*MUD_DARK, 150)),
        ]:
            pygame.draw.circle(s, c, (int(dx), int(dy)), int(r))
        # highlight specks
        for (dx, dy) in [(0.20, 0.65), (0.80, 0.25), (0.40, 0.20), (0.65, 0.75)]:
            pygame.draw.circle(s, (*MUD_HL, 100), (int(TILE * dx), int(TILE * dy)), 1)

    # ---------- maze (cached on a surface) ----------

    def mark_maze_dirty(self):
        self.maze_dirty = True

    def _draw_floor(self, maze):
        self.maze_surf.fill(BG_DEEP)
        # base floor + mud tiles
        for x in range(maze.cols):
            for y in range(maze.rows):
                c = maze.cell(x, y)
                rx, ry = x * TILE, y * TILE
                if c.is_mud:
                    pygame.draw.rect(self.maze_surf, MUD, (rx, ry, TILE, TILE))
                    self.maze_surf.blit(self._mud_overlay, (rx, ry))
                else:
                    pygame.draw.rect(self.maze_surf, FLOOR, (rx, ry, TILE, TILE))
                    # tiny center dot for subtle texture (skipped on cells with pellets)
                    if not c.has_pellet:
                        pygame.draw.circle(self.maze_surf, FLOOR_DOT,
                                           (rx + TILE // 2, ry + TILE // 2), 1)

    def _draw_walls(self, maze):
        """Walls as fat tubes: dark outline, main body, bright inner highlight.
        Each shared wall is drawn once (N + W per cell; S/E only at boundary)."""
        t = WALL_THICK
        outline_t = t + 4
        hl_t = max(2, t // 3)

        def seg(color, thick, a, b):
            pygame.draw.line(self.maze_surf, color, a, b, thick)
            # rounded caps
            r = thick // 2
            pygame.draw.circle(self.maze_surf, color, a, r)
            pygame.draw.circle(self.maze_surf, color, b, r)

        # Three-pass per wall: dark outline (widest) -> main -> highlight (thin)
        for layer_color, layer_t in ((WALL_DARK, outline_t), (WALL, t), (WALL_HL, hl_t)):
            for x in range(maze.cols):
                for y in range(maze.rows):
                    c = maze.cell(x, y)
                    rx, ry = x * TILE, y * TILE
                    if c.walls["N"]:
                        seg(layer_color, layer_t, (rx, ry), (rx + TILE, ry))
                    if c.walls["W"]:
                        seg(layer_color, layer_t, (rx, ry), (rx, ry + TILE))
                    if y == maze.rows - 1 and c.walls["S"]:
                        seg(layer_color, layer_t, (rx, ry + TILE), (rx + TILE, ry + TILE))
                    if x == maze.cols - 1 and c.walls["E"]:
                        seg(layer_color, layer_t, (rx + TILE, ry), (rx + TILE, ry + TILE))

        # corner studs at every grid intersection that touches at least one wall
        stud_r = t // 2 + 1
        for x in range(maze.cols + 1):
            for y in range(maze.rows + 1):
                if self._has_wall_at_corner(maze, x, y):
                    cx, cy = x * TILE, y * TILE
                    pygame.draw.circle(self.maze_surf, WALL_DARK, (cx, cy), stud_r + 1)
                    pygame.draw.circle(self.maze_surf, WALL, (cx, cy), stud_r)
                    pygame.draw.circle(self.maze_surf, WALL_HL, (cx, cy), max(1, stud_r // 3))

    @staticmethod
    def _has_wall_at_corner(maze, x, y):
        # Check the four cells meeting at corner (x, y) for a wall touching this corner.
        for cx, cy in ((x - 1, y - 1), (x, y - 1), (x - 1, y), (x, y)):
            if not (0 <= cx < maze.cols and 0 <= cy < maze.rows):
                # boundary corner — there is an outer wall here
                return True
            c = maze.cell(cx, cy)
            # any wall of that cell touches this corner
            if (cx + 1 == x and (c.walls["N"] or c.walls["E"])) or \
               (cx == x and (c.walls["N"] or c.walls["W"])) or \
               (cx + 1 == x and cy + 1 == y and (c.walls["S"] or c.walls["E"])) or \
               (cx == x and cy + 1 == y and (c.walls["S"] or c.walls["W"])):
                return True
        return False

    def _bake_maze(self, maze):
        self._draw_floor(maze)
        self._draw_walls(maze)
        self.maze_dirty = False

    # ---------- frame ----------

    def draw_frame(self, game):
        self.time += 1 / 60  # approximate; only used for anim phases

        if self.maze_dirty:
            self._bake_maze(game.maze)

        self.screen.fill(BLACK)
        self.screen.blit(self.maze_surf, (0, HUD_HEIGHT))

        if game.show_paths:
            self._draw_paths(game)

        self._draw_pellets(game)

        # subtle glow under entities
        self.glow_surf.fill((0, 0, 0, 0))
        for e in game.enemies:
            color = ENEMY_BFS if e.kind == "bfs" else ENEMY_DIJK
            self._soft_glow(self.glow_surf, e.center()[0], e.center()[1] - HUD_HEIGHT, TILE * 0.95, color, 70)
        self._soft_glow(self.glow_surf,
                        game.player.center()[0],
                        game.player.center()[1] - HUD_HEIGHT,
                        TILE * 0.85, PLAYER, 70)
        self.screen.blit(self.glow_surf, (0, HUD_HEIGHT))

        # entities
        for e in game.enemies:
            self._draw_enemy(e, game.player)
        self._draw_player(game.player)

        self._draw_hud(game)

        if game.state == "paused":
            self._overlay("PAUSED", "Tekan P untuk lanjut", TEXT)
        elif game.state == "game_over":
            self._overlay("GAME OVER", "Tekan R untuk restart", LOSE_COLOR)
        elif game.state == "win":
            self._overlay("KAMU MENANG!", "Tekan R untuk main lagi", WIN_COLOR)

    # ---------- pellets ----------

    def _draw_pellets(self, game):
        pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)
        base_r = max(2, TILE // 10)
        for x in range(game.maze.cols):
            for y in range(game.maze.rows):
                c = game.maze.cell(x, y)
                if not c.has_pellet:
                    continue
                cx = x * TILE + TILE // 2
                cy = y * TILE + TILE // 2 + HUD_HEIGHT
                # soft outer glow
                pygame.draw.circle(self.screen, PELLET_GLOW, (cx, cy), base_r + 2 + int(pulse))
                pygame.draw.circle(self.screen, PELLET, (cx, cy), base_r)

    # ---------- entities ----------

    def _draw_player(self, p):
        cx, cy = p.center()
        r = TILE // 2 - 4
        # mouth animation: open/close
        mouth_open = (math.sin(self.time * 14) + 1) * 0.5  # 0..1
        mouth = 0.05 + mouth_open * 0.55  # 0.05..0.6 radians half-angle
        fx, fy = p.facing
        if fx == 0 and fy == 0:
            fx = 1  # default face right when idle
        ang = math.atan2(fy, fx)

        # body with subtle highlight
        pygame.draw.circle(self.screen, PLAYER_DARK, (cx, cy), r + 1)
        pygame.draw.circle(self.screen, PLAYER, (cx, cy), r)
        pygame.draw.circle(self.screen, PLAYER_HL, (cx - r // 3, cy - r // 3), max(2, r // 4))

        # mouth wedge (background-colored triangle from center to two points on rim)
        p1 = (cx + math.cos(ang - mouth) * (r + 3), cy + math.sin(ang - mouth) * (r + 3))
        p2 = (cx + math.cos(ang + mouth) * (r + 3), cy + math.sin(ang + mouth) * (r + 3))
        pygame.draw.polygon(self.screen, BLACK, [(cx, cy), p1, p2])

    def _draw_enemy(self, e, player):
        cx, cy = e.center()
        r = TILE // 2 - 4
        if e.kind == "bfs":
            body, hl = ENEMY_BFS, ENEMY_BFS_HL
        else:
            body, hl = ENEMY_DIJK, ENEMY_DIJK_HL

        # Body: dome + rectangle bottom + animated zigzag skirt
        top = cy - r
        bot = cy + r
        pygame.draw.circle(self.screen, body, (cx, top + r), r)
        pygame.draw.rect(self.screen, body, (cx - r, top + r, r * 2, r - 2))

        # wavy bottom
        zigs = 4
        zig_w = (2 * r) / zigs
        wave = math.sin(self.time * 8 + e.cx * 0.7) * (r * 0.20)
        pts = [(cx - r, bot)]
        for i in range(zigs):
            x0 = cx - r + i * zig_w
            mid_y = bot - r * 0.35 + (wave if i % 2 == 0 else -wave)
            pts.append((x0 + zig_w / 2, mid_y))
            pts.append((x0 + zig_w, bot))
        pygame.draw.polygon(self.screen, body, pts)

        # highlight curl on top-left
        pygame.draw.arc(self.screen, hl,
                        (cx - r + 2, top + 2, r, r), math.radians(120), math.radians(210), 2)

        # eyes: pupils point toward player direction
        eye_r = max(3, r // 3)
        eye_dx = r // 2
        eye_dy = r // 4
        for sx in (-1, 1):
            ex, ey = cx + sx * eye_dx, cy - eye_dy
            pygame.draw.circle(self.screen, ENEMY_EYE, (ex, ey), eye_r)
            # pupil offset toward player
            dx = player.center()[0] - ex
            dy = player.center()[1] - ey
            d = math.hypot(dx, dy) or 1
            off = eye_r * 0.4
            px = ex + int(dx / d * off)
            py = ey + int(dy / d * off)
            pygame.draw.circle(self.screen, ENEMY_PUPIL, (px, py), max(2, eye_r // 2))

    # ---------- glow util ----------

    @staticmethod
    def _soft_glow(surf, cx, cy, radius, color, alpha):
        # cheap radial glow: a few concentric translucent circles
        steps = 4
        for i in range(steps, 0, -1):
            r = int(radius * (i / steps))
            a = int(alpha * (i / steps) * 0.6)
            pygame.draw.circle(surf, (*color, a), (int(cx), int(cy)), r)

    # ---------- AI paths ----------

    def _draw_paths(self, game):
        self.path_surf.fill((0, 0, 0, 0))
        for e in game.enemies:
            if len(e.path) < 2:
                continue
            color = ENEMY_BFS if e.kind == "bfs" else ENEMY_DIJK
            pts = [(x * TILE + TILE // 2, y * TILE + TILE // 2) for (x, y) in e.path]
            # glow line
            pygame.draw.lines(self.path_surf, (*color, 60), False, pts, 8)
            pygame.draw.lines(self.path_surf, (*color, 160), False, pts, 3)
            for (x, y) in e.path:
                pygame.draw.circle(self.path_surf, (*color, 180),
                                   (x * TILE + TILE // 2, y * TILE + TILE // 2), 3)
        self.screen.blit(self.path_surf, (0, HUD_HEIGHT))

    # ---------- HUD ----------

    def _draw_hud(self, game):
        pygame.draw.rect(self.screen, HUD_BG, (0, 0, WIDTH, HUD_HEIGHT))
        # bottom edge line with glow
        pygame.draw.line(self.screen, HUD_LINE, (0, HUD_HEIGHT - 2), (WIDTH, HUD_HEIGHT - 2), 2)
        pygame.draw.line(self.screen, WALL_HL, (0, HUD_HEIGHT - 1), (WIDTH, HUD_HEIGHT - 1), 1)

        # left: score + pellets
        s1 = self.font_mid.render(f"SCORE  {game.score:04d}", True, TEXT)
        self.screen.blit(s1, (14, 10))
        s2 = self.font_small.render(
            f"PELLETS  {game.pellets_total - game.pellets_left}/{game.pellets_total}",
            True, TEXT_DIM,
        )
        self.screen.blit(s2, (14, 42))

        # center: legend
        cx = WIDTH // 2
        leg_y = 12
        # BFS chip
        pygame.draw.circle(self.screen, ENEMY_BFS, (cx - 88, leg_y + 8), 8)
        pygame.draw.circle(self.screen, ENEMY_BFS_HL, (cx - 91, leg_y + 5), 3)
        self.screen.blit(self.font_small.render("BFS", True, TEXT), (cx - 76, leg_y + 1))
        # Dijkstra chip
        pygame.draw.circle(self.screen, ENEMY_DIJK, (cx + 6, leg_y + 8), 8)
        pygame.draw.circle(self.screen, ENEMY_DIJK_HL, (cx + 3, leg_y + 5), 3)
        self.screen.blit(self.font_small.render("Dijkstra", True, TEXT), (cx + 18, leg_y + 1))
        # captions
        self.screen.blit(
            self.font_small.render("Maze gen: DFS recursive-backtracking", True, TEXT_DIM),
            (cx - 140, leg_y + 24),
        )
        self.screen.blit(
            self.font_small.render("D toggle path   P pause   R restart   Esc quit",
                                   True, TEXT_DIM),
            (cx - 165, leg_y + 44),
        )

        # right: lives as little pacmen
        for i in range(game.lives):
            px = WIDTH - 26 - i * 30
            py = 22
            pygame.draw.circle(self.screen, PLAYER_DARK, (px, py), 11)
            pygame.draw.circle(self.screen, PLAYER, (px, py), 10)
            pygame.draw.polygon(self.screen, HUD_BG,
                                [(px, py), (px + 14, py - 7), (px + 14, py + 7)])
        self.screen.blit(self.font_small.render("LIVES", True, TEXT_DIM), (WIDTH - 60, 44))

    # ---------- overlays ----------

    def _overlay(self, title, sub, color):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 180))
        self.screen.blit(veil, (0, 0))

        # title with subtle shadow
        shadow = self.font_big.render(title, True, (0, 0, 0))
        t = self.font_big.render(title, True, color)
        self.screen.blit(shadow,
                         (WIDTH // 2 - t.get_width() // 2 + 3, HEIGHT // 2 - 50 + 3))
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 50))

        s = self.font_mid.render(sub, True, TEXT)
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 14))
