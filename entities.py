from settings import (
    TILE, HUD_HEIGHT,
    PLAYER_SPEED, ENEMY_BFS_SPEED, ENEMY_DIJK_SPEED,
)


class Entity:
    def __init__(self, cx, cy, speed):
        self.cx = cx
        self.cy = cy
        self.tx = cx
        self.ty = cy
        self.px = cx * TILE
        self.py = cy * TILE + HUD_HEIGHT
        self.speed = speed
        self.moving = False

    def at_cell(self):
        return (self.cx, self.cy)

    def reset(self, cx, cy):
        self.cx = self.tx = cx
        self.cy = self.ty = cy
        self.px = cx * TILE
        self.py = cy * TILE + HUD_HEIGHT
        self.moving = False

    def set_target(self, tx, ty):
        if (tx, ty) != (self.cx, self.cy):
            self.tx = tx
            self.ty = ty
            self.moving = True

    def update(self, dt, speed_mult=1.0):
        if not self.moving:
            return
        target_px = self.tx * TILE
        target_py = self.ty * TILE + HUD_HEIGHT
        dx = target_px - self.px
        dy = target_py - self.py
        step = self.speed * TILE * dt * speed_mult
        if abs(dx) <= step and abs(dy) <= step:
            self.px = target_px
            self.py = target_py
            self.cx = self.tx
            self.cy = self.ty
            self.moving = False
            return
        if dx > 0:   self.px += step
        elif dx < 0: self.px -= step
        if dy > 0:   self.py += step
        elif dy < 0: self.py -= step

    def center(self):
        return (self.px + TILE // 2, self.py + TILE // 2)


class Player(Entity):
    def __init__(self, cx, cy):
        super().__init__(cx, cy, PLAYER_SPEED)
        self.cur_dir = (0, 0)
        self.next_dir = (0, 0)
        self.facing = (1, 0)
        self.mouth_phase = 0.0


class Enemy(Entity):
    def __init__(self, cx, cy, kind):
        if kind == "bfs":
            super().__init__(cx, cy, ENEMY_BFS_SPEED)
        else:
            super().__init__(cx, cy, ENEMY_DIJK_SPEED)
        self.kind = kind
        self.path = []
        self.recompute_timer = 0.0
        self.spawn = (cx, cy)