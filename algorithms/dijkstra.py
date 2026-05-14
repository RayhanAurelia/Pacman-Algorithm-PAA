import heapq
from settings import MUD_COST, NORMAL_COST


def dijkstra_path(maze, start, goal):
    if start == goal:
        return [start]

    dist = {start: 0}
    parent = {start: None}
    pq = [(0, start)]

    while pq:
        d, cur = heapq.heappop(pq)
        if cur == goal:
            return _reconstruct(parent, cur)
        if d > dist[cur]:
            continue
        for nxt in maze.neighbors_open(*cur):
            w = MUD_COST if maze.cell(*nxt).is_mud else NORMAL_COST
            nd = d + w
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                parent[nxt] = cur
                heapq.heappush(pq, (nd, nxt))
    return []


def _reconstruct(parent, end):
    path = []
    n = end
    while n is not None:
        path.append(n)
        n = parent[n]
    path.reverse()
    return path
