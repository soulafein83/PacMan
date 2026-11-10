"""Maze definition and tile helpers.

Pure Python module with no dependency on pyxel, so it can be
imported and unit-tested directly.

Tile legend (one character per cell):
    #  wall
    -  ghost house door
    o  power pellet
    .  pellet
     (space)  empty walkable floor (no pellet)
"""

TILE_SIZE = 4

# 28 columns x 26 rows. Every row is exactly 28 characters.
MAZE_MAP = [
    "############################",                       # 0
    "#............##............#",                     # 1
    "#..####.####.##.####.####..#",                     # 2
    "#..........................#",                     # 3
    "#o..#..#..###..#..###..#..o#",                     # 4
    "#####.##.#####.##.#####.####",                     # 5
    "#..........................#",                     # 6
    "#....##..##......##..##....#",                     # 7
    "#....##..##......##..##....#",                     # 8
    "#....##..##......##..##....#",                     # 9
    "#..........................#",                     # 10
    "#....##..##......##..##....#",                     # 11
    "#....##..## #--# ##..##....#",                     # 12
    "#....##..## #  # ##..##....#",                     # 13
    "#....##..## #### ##..##....#",                     # 14
    "#....##..##......##..##....#",                     # 15
    "#....##..##......##..##....#",                     # 16
    "#....##..##......##..##....#",                     # 17
    " .......................... ",                     # 18
    "#..........................#",                     # 19
    "#####.##.#####.##.#####.####",                     # 20
    "#o..#..#..###..#..###..#..o#",                     # 21
    "#..........................#",                     # 22
    "#..####.####.##.####.####..#",                     # 23
    "#............##............#",                     # 24
    "############################",                       # 25
]

WALKABLE = {" ", "-", "o", "."}
WALL_CHARS = {"#", "-"}

MAZE_WIDTH = len(MAZE_MAP[0])          # 28
MAZE_HEIGHT = len(MAZE_MAP)            # 26
MAZE_PIXEL_W = MAZE_WIDTH * TILE_SIZE  # 112
MAZE_PIXEL_H = MAZE_HEIGHT * TILE_SIZE  # 104

# Row with the horizontal tunnel (open at both edges, wraps around).
TUNNEL_ROW = 18


def tile_at(col, row):
    """Return the tile char at (col, row). Walls/doors return their char,
    out-of-bounds returns '#'."""
    if not (0 <= col < MAZE_WIDTH and 0 <= row < MAZE_HEIGHT):
        return "#"
    return MAZE_MAP[row][col]


def is_wall(col, row):
    return tile_at(col, row) == "#"


def is_walkable(col, row):
    return tile_at(col, row) in WALKABLE


def pellets():
    """Yield (col, row) of every pellet ('.') and power pellet ('o')."""
    for row in range(MAZE_HEIGHT):
        for col in range(MAZE_WIDTH):
            if tile_at(col, row) in (".", "o"):
                yield (col, row)
