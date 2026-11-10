"""Game entities — pure Python, no pyxel (unit-testable headless).

Coordinates are *maze pixels*: the maze origin is (0, 0), the render
layer adds OX/OY. Movement is 1 px per frame on a 4 px grid, so tile
corners are always multiples of 4 and "at an intersection" means both
coordinates are multiples of 4.
"""
import maze

TILE = maze.TILE_SIZE
SPEED = 1  # px per frame
TUNNEL_ROW = maze.TUNNEL_ROW

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)
DIR_KEYS = {"up": UP, "down": DOWN, "left": LEFT, "right": RIGHT}

# Spawn at the top-left corner of tile (13, 11) — the open row above
# the ghost house.
START_X = 13 * TILE
START_Y = 11 * TILE


def _walkable(x, y):
    """Is the tile containing maze pixel (x, y) walkable?"""
    return maze.is_walkable(x // TILE, y // TILE)


class Pacman:
    def __init__(self, x=START_X, y=START_Y):
        self.x = x
        self.y = y
        self.dir = None        # (dx, dy) or None while waiting for input
        self.queued = None     # direction buffered from the player

    def at_intersection(self):
        return self.x % TILE == 0 and self.y % TILE == 0

    def _ahead(self, d):
        """The maze pixel we would step into from here along d,
        wrapped through the tunnel on row 18."""
        nx, ny = self.x + d[0] * SPEED, self.y + d[1] * SPEED
        if ny // TILE == TUNNEL_ROW:
            if nx < 0:
                nx += maze.MAZE_PIXEL_W
            elif nx >= maze.MAZE_PIXEL_W:
                nx -= maze.MAZE_PIXEL_W
        return nx, ny

    def _can_enter(self, d):
        """Is the tile we would step into from here along d walkable?"""
        nx, ny = self._ahead(d)
        return _walkable(nx, ny)

    def update(self, desired=None):
        """Advance one frame. `desired` is a DIR_KEYS name just pressed."""
        if desired is not None:
            self.queued = DIR_KEYS[desired]

        if self.dir is None:
            # waiting for the first direction input
            if self.queued is not None and self._can_enter(self.queued):
                self.dir = self.queued
            else:
                return

        # direction change:
        #  - at an intersection: any buffered direction (incl. reverse)
        #  - mid-tile: only a perpendicular turn, if that tile is open
        if self.queued is not None:
            d = self.queued
            allowed = (
                self.at_intersection()
                or (d[0] != 0) != (self.dir[0] != 0)  # different axes
            )
            if allowed and self._can_enter(d):
                self.dir = d
                self.queued = None

        # move (1 px)
        nx, ny = self._ahead(self.dir)
        if _walkable(nx, ny):
            self.x, self.y = nx, ny
        # else: blocked — we sit exactly on a tile corner here, so the
        # player can steer at the next frame.
