import random


def generate_maze(maze, start=(0, 0)):
    for col in maze.grid:
        for c in col:
            c.visited = False
            c.walls = {"N": True, "S": True, "E": True, "W": True}

    stack = [start]
    maze.cell(*start).visited = True

    while stack:
        cx, cy = stack[-1]
        unvisited = []
        for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            nx, ny = cx + dx, cy + dy
            if maze.in_bounds(nx, ny) and not maze.cell(nx, ny).visited:
                unvisited.append((nx, ny))

        if unvisited:
            nx, ny = random.choice(unvisited)
            maze.remove_wall((cx, cy), (nx, ny))
            maze.cell(nx, ny).visited = True
            stack.append((nx, ny))
        else:
            stack.pop()
