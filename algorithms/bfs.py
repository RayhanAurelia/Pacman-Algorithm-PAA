from collections import deque


def bfs_path(maze, start, goal):
    if start == goal:
        return [start]

    parent = {start: None}
    q = deque([start])

    while q:
        cur = q.popleft()
        if cur == goal:
            return _reconstruct(parent, cur)
        for nxt in maze.neighbors_open(*cur):
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)
    return []


def _reconstruct(parent, end):
    path = []
    n = end
    while n is not None:
        path.append(n)
        n = parent[n]
    path.reverse()
    return path
