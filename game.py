import math
import pygame
from settings import (
    COLS, ROWS, START_LIVES, RECOMPUTE_INTERVAL,
    MUD_SLOWDOWN, TILE,
)
from maze import Maze
from entities import Player, Enemy
from algorithms import generate_maze, bfs_path, dijkstra_path


class Game:
    def __init__(self, renderer):
        self.renderer = renderer
        self.state = "playing"
        self.show_paths = False
        self.score = 0
        self.lives = START_LIVES
        self.player = None
        self.enemies = []
        self.maze = None
        self.pellets_total = 0
        self.pellets_left = 0
        self.invulnerable = 0.0
        self.reset()

    # ---------- setup ----------

    def reset(self):
        self.score = 0
        self.lives = START_LIVES
        self._new_level()

    def _new_level(self):
        self.maze = Maze(COLS, ROWS)
        generate_maze(self.maze, start=(0, 0))
        self.maze.add_loops(int((COLS * ROWS) * 0.10))

        player_spawn = (COLS // 2, ROWS // 2)
        bfs_spawn    = (0, 0)
        dijk_spawn   = (COLS - 1, ROWS - 1)

        self.maze.assign_mud(exclude={player_spawn, bfs_spawn, dijk_spawn})

        self.player  = Player(*player_spawn)
        self.enemies = [
            Enemy(*bfs_spawn,  kind="bfs"),
            Enemy(*dijk_spawn, kind="dijkstra"),
        ]

        self.maze.cell(*player_spawn).has_pellet = False
        for e in self.enemies:
            self.maze.cell(*e.spawn).has_pellet = False

        self.pellets_total = sum(
            1 for x in range(COLS) for y in range(ROWS)
            if self.maze.cell(x, y).has_pellet
        )
        self.pellets_left = self.pellets_total
        self.invulnerable = 1.5
        self.state = "playing"
        self.renderer.mark_maze_dirty()

    def _respawn_after_death(self):
        self.player.reset(COLS // 2, ROWS // 2)
        self.enemies[0].reset(0, 0)
        self.enemies[1].reset(COLS - 1, ROWS - 1)
        for e in self.enemies:
            e.path = []
            e.recompute_timer = 0.0
        self.invulnerable = 1.5

    # ---------- input ----------

    _DIR_KEYS = None  # filled lazily after pygame is imported in main

    def handle_event(self, ev):
        if ev.type != pygame.KEYDOWN:
            return

        if Game._DIR_KEYS is None:
            Game._DIR_KEYS = {
                pygame.K_UP:    (0, -1), pygame.K_w: (0, -1),
                pygame.K_DOWN:  (0,  1), pygame.K_s: (0,  1),
                pygame.K_LEFT:  (-1, 0), pygame.K_a: (-1, 0),
                pygame.K_RIGHT: (1,  0), pygame.K_d: (1,  0),
            }

        if ev.key == pygame.K_p and self.state in ("playing", "paused"):
            self.state = "paused" if self.state == "playing" else "playing"
        elif ev.key == pygame.K_r:
            self.reset()
        elif ev.key == pygame.K_SLASH:
            self.show_paths = not self.show_paths
        elif ev.key in Game._DIR_KEYS:
            self.player.next_dir = Game._DIR_KEYS[ev.key]

    # ---------- update ----------

    def update(self, dt):
        if self.state != "playing":
            return

        self.invulnerable = max(0.0, self.invulnerable - dt)
        self._update_player(dt)
        for e in self.enemies:
            self._update_enemy(e, dt)
        self._collect_pellets()
        self._check_collisions()

        if self.pellets_left == 0:
            self.state = "win"

    def _can_move(self, fx, fy, tx, ty):
        if not self.maze.in_bounds(tx, ty):
            return False
        return (tx, ty) in self.maze.neighbors_open(fx, fy)

    # ------------------------------------------------------------------
    # Corner rounding
    # ------------------------------------------------------------------

    # Max pixels off-axis we'll silently correct. 40% of a tile is
    # generous enough to feel forgiving without being sloppy.
    SNAP_THRESHOLD = TILE * 0.4

    def _corner_snap(self, p, ndx, ndy):
        """
        When the player wants to turn but is slightly mis-aligned with the
        target corridor, nudge their pixel position onto the axis and check
        again.  Only touches the axis perpendicular to the desired direction.

        Returns True if the snap brought them into alignment (caller should
        then retry _can_move), False if they were too far off to correct.
        """
        from settings import HUD_HEIGHT
        # Centre of the cell Pac-Man currently occupies, in pixel space
        cell_px = p.cx * TILE + TILE // 2
        cell_py = p.cy * TILE + HUD_HEIGHT + TILE // 2
        # Pac-Man's current pixel centre
        player_px = p.px + TILE // 2
        player_py = p.py + TILE // 2

        if ndy != 0:
            # Turning vertically — must be aligned on X
            off = player_px - cell_px
            if abs(off) <= self.SNAP_THRESHOLD:
                p.px -= off
                return True

        if ndx != 0:
            # Turning horizontally — must be aligned on Y
            off = player_py - cell_py
            if abs(off) <= self.SNAP_THRESHOLD:
                p.py -= off
                return True

        return False

    # ------------------------------------------------------------------
    # Player update
    # ------------------------------------------------------------------

    def _update_player(self, dt):
        p = self.player
        p.mouth_phase += dt * 12

        slow = MUD_SLOWDOWN if self.maze.cell(p.cx, p.cy).is_mud else 1.0
        p.update(dt, speed_mult=slow)

        ndx, ndy = p.next_dir

        if not p.moving:
            # ── Landed on a cell ───────────────────────────────────────
            # Try the buffered direction first. next_dir persists until
            # the player presses something new, so this retries every
            # frame automatically — the turn fires the instant it's valid.
            if (ndx, ndy) != (0, 0):
                nx, ny = p.cx + ndx, p.cy + ndy
                if self._can_move(p.cx, p.cy, nx, ny):
                    p.set_target(nx, ny)
                    p.cur_dir = (ndx, ndy)
                    p.facing  = (ndx, ndy)
                    return
                # Not aligned — try nudging onto the corridor axis first
                if self._corner_snap(p, ndx, ndy) and self._can_move(p.cx, p.cy, nx, ny):
                    p.set_target(nx, ny)
                    p.cur_dir = (ndx, ndy)
                    p.facing  = (ndx, ndy)
                    return

            # Buffered turn not valid yet; keep sliding in current dir.
            cdx, cdy = p.cur_dir
            if (cdx, cdy) != (0, 0):
                nx, ny = p.cx + cdx, p.cy + cdy
                if self._can_move(p.cx, p.cy, nx, ny):
                    p.set_target(nx, ny)
                    p.facing = (cdx, cdy)
                else:
                    p.cur_dir = (0, 0)

    # ------------------------------------------------------------------

    def _update_enemy(self, e, dt):
        e.recompute_timer -= dt
        slow = MUD_SLOWDOWN if self.maze.cell(e.cx, e.cy).is_mud else 1.0
        e.update(dt, speed_mult=slow)

        if e.moving:
            return

        goal = self.player.at_cell()
        if e.recompute_timer <= 0 or len(e.path) < 2 or (e.path and e.path[-1] != goal):
            start = e.at_cell()
            if e.kind == "bfs":
                e.path = bfs_path(self.maze, start, goal)
            else:
                e.path = dijkstra_path(self.maze, start, goal)
            e.recompute_timer = RECOMPUTE_INTERVAL

        if len(e.path) >= 2:
            nx, ny = e.path[1]
            e.set_target(nx, ny)
            e.path = e.path[1:]

    def _collect_pellets(self):
        c = self.maze.cell(self.player.cx, self.player.cy)
        if c.has_pellet:
            c.has_pellet = False
            self.score += 10
            self.pellets_left -= 1

    def _check_collisions(self):
        if self.invulnerable > 0:
            return
        px, py = self.player.center()
        for e in self.enemies:
            ex, ey = e.center()
            if math.hypot(px - ex, py - ey) < TILE * 0.55:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = "game_over"
                else:
                    self._respawn_after_death()
                return