"""Unit tests for maze.py (pure logic, no pyxel needed)."""
from collections import deque

import maze


def test_all_rows_are_28_chars():
    for i, row in enumerate(maze.MAZE_MAP):
        assert len(row) == maze.MAZE_WIDTH, f"row {i} has width {len(row)}"


def test_maze_dimensions():
    assert maze.MAZE_WIDTH == 28
    assert maze.MAZE_HEIGHT == 26
    assert maze.MAZE_PIXEL_W == 112
    assert maze.MAZE_PIXEL_H == 104


def test_every_walkable_cell_is_reachable():
    """Flood-fill from the first walkable cell must reach all walkable cells."""
    start = next((c, r) for r in range(maze.MAZE_HEIGHT)
                 for c in range(maze.MAZE_WIDTH) if maze.is_walkable(c, r))
    seen = {start}
    queue = deque([start])
    while queue:
        c, r = queue.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if (maze.is_walkable(nc, nr) and (nc, nr) not in seen):
                seen.add((nc, nr))
                queue.append((nc, nr))
    total = sum(1 for r in range(maze.MAZE_HEIGHT)
                for c in range(maze.MAZE_WIDTH) if maze.is_walkable(c, r))
    assert len(seen) == total


def test_four_power_pellets_exist():
    powers = sum(1 for row in maze.MAZE_MAP for ch in row if ch == "o")
    assert powers == 4


def test_ghost_house_door_exists():
    doors = [(c, r) for r in range(maze.MAZE_HEIGHT)
             for c in range(maze.MAZE_WIDTH) if maze.MAZE_MAP[r][c] == "-"]
    assert len(doors) == 2
    # The two door tiles are adjacent, centered horizontally.
    (c1, r1), (c2, r2) = doors
    assert r1 == r2 and abs(c1 - c2) == 1
