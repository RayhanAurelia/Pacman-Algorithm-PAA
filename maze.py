import random
from settings import MUD_RATIO


class Cell:
    __slots__ = ("x", "y", "walls", "visited", "is_mud", "has_pellet")

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {"N": True, "S": True, "E": True, "W": True}
        self.visited = False
        self.is_mud = False
        self.has_pellet = True


class Maze:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = [[Cell(x, y) for y in range(rows)] for x in range(cols)]

    def cell(self, x, y):
        return self.grid[x][y]

    def in_bounds(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows

    def neighbors_open(self, x, y):
        """Cells reachable from (x,y) — no wall in between."""
        out = []
        c = self.cell(x, y)
        if not c.walls["N"] and self.in_bounds(x, y - 1):
            out.append((x, y - 1))
        if not c.walls["S"] and self.in_bounds(x, y + 1):
            out.append((x, y + 1))
        if not c.walls["E"] and self.in_bounds(x + 1, y):
            out.append((x + 1, y))
        if not c.walls["W"] and self.in_bounds(x - 1, y):
            out.append((x - 1, y))
        return out

    def remove_wall(self, a, b):
        ax, ay = a
        bx, by = b
        if bx == ax + 1:
            self.cell(ax, ay).walls["E"] = False
            self.cell(bx, by).walls["W"] = False
        elif bx == ax - 1:
            self.cell(ax, ay).walls["W"] = False
            self.cell(bx, by).walls["E"] = False
        elif by == ay + 1:
            self.cell(ax, ay).walls["S"] = False
            self.cell(bx, by).walls["N"] = False
        elif by == ay - 1:
            self.cell(ax, ay).walls["N"] = False
            self.cell(bx, by).walls["S"] = False

    def add_loops(self, count):
        """Knock down extra walls to add cycles — makes chasing more interesting."""
        attempts = 0
        added = 0
        while added < count and attempts < count * 20:
            attempts += 1
            x = random.randrange(self.cols)
            y = random.randrange(self.rows)
            c = self.cell(x, y)
            sides = [s for s, v in c.walls.items() if v]
            if not sides:
                continue
            side = random.choice(sides)
            dx, dy = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[side]
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                self.remove_wall((x, y), (nx, ny))
                added += 1

    def assign_mud(self, exclude=()):
        """Mark a fraction of cells as mud (weighted tiles for Dijkstra)."""
        all_cells = [(x, y) for x in range(self.cols) for y in range(self.rows)
                     if (x, y) not in exclude]
        random.shuffle(all_cells)
        count = int(len(all_cells) * MUD_RATIO)
        for (x, y) in all_cells[:count]:
            c = self.cell(x, y)
            c.is_mud = True
            c.has_pellet = False