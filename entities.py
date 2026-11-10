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
    """Is the tile containing maze pixel (x, y) walkable by pacman?

    The ghost-house door ('-') is closed for pacman: ghosts leave
    through it, he cannot enter.
    """
    col, row = x // TILE, y // TILE
    return maze.tile_at(col, row) != "-" and maze.is_walkable(col, row)


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


PELLET_SCORE = 10


class Game:
    """One round of the game: pacman + pellet field + score.

    Pure logic — no pyxel. The pyxel layer (main.py) owns the
    session-high score across rounds.
    """

    # One ghost leaves the house every 3 s (180 frames), classic
    # stagger: Blinky first, then Inky, Pinky, Clyde.
    RELEASE_STAGGER_FRAMES = (0, 180, 360, 540)

    def __init__(self):
        self.pacman = Pacman()
        self.pellets = set(maze.pellets())  # {(col, row), ...}
        # spawn tile has no pellet (like the original): no free points
        self.pellets.discard((START_X // TILE, START_Y // TILE))
        self.score = 0
        self.frame = 0
        self.ghosts = [
            Ghost(kind,
                  release_frame=release,
                  bob_dir=-1 if i % 2 else 1)
            for i, (kind, release) in enumerate(zip(GHOST_KINDS,
                                                    self.RELEASE_STAGGER_FRAMES))
        ]

    def _current_tile(self):
        return (self.pacman.x // TILE, self.pacman.y // TILE)

    def pacman_tile(self):
        return self._current_tile()

    def ghost_tile(self, kind):
        for g in self.ghosts:
            if g.kind == kind:
                return g.tile()
        raise KeyError(kind)

    def update(self, desired=None):
        """Advance one frame; eats the pellet on pacman's tile."""
        self.frame += 1
        self.pacman.update(desired)
        tile = self._current_tile()
        if tile in self.pellets:
            self.pellets.discard(tile)
            self.score += PELLET_SCORE
        for g in self.ghosts:
            g.update(self)

    def maze_empty(self):
        """True when every pellet is gone (level-advance condition;
        the advance mechanic itself lands in step 6)."""
        return not self.pellets


# --- ghosts (step 4) -------------------------------------------------------

# Ghost life-cycle states.
IN_HOUSE = "in_house"    # bobbing inside the house
LEAVING = "leaving"      # sliding to the door, rising through it
OUTSIDE = "outside"      # roaming the maze with tile-based AI
# ("fleeing" arrives with step 5's power pellets)

BLINKY, PINKY, INKY, CLYDE = "blinky", "pinky", "inky", "clyde"
# Release order matches the arcade: Blinky, Inky, Pinky, Clyde.
GHOST_KINDS = (BLINKY, INKY, PINKY, CLYDE)

GHOST_SPEED = 1  # px per frame (same as pacman; halved in step 5)

# The house: interior tile row is 13, door tiles are (13,12)/(14,12),
# the open row above the house is 11.
HOUSE_X = 13 * TILE + 2          # 54 — center of the door
HOUSE_BOB_MIN = 13 * TILE        # 52 — top of the interior row
HOUSE_BOB_MAX = 13 * TILE + 1    # 53 — 1 px bob (the 4 px room fits a 4 px ghost)
HOUSE_EXIT_Y = 11 * TILE          # 44 — top of the open row 11
HOUSE_EXIT_X = 13 * TILE          # 52 — nearest grid line of the open row

# Tie-break order when two edges are equidistant from the target.
EDGE_PRIORITY = (UP, LEFT, RIGHT, DOWN)

# Corners used by Clyde's "flee" target.
CORNER_TILES = ((1, 1), (26, 1), (1, 24), (26, 24))


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Ghost:
    """One ghost. Movement is 1 px/frame like pacman; direction
    decisions happen only at tile corners (both coords % 4 == 0)."""

    def __init__(self, kind, x=HOUSE_X, y=HOUSE_BOB_MIN,
                 release_frame=0, bob_dir=1):
        self.kind = kind
        self.x = x
        self.y = y
        self.dir = UP          # facing up while bobbing/rising
        self.state = IN_HOUSE
        self.release_frame = release_frame
        self.bob_dir = bob_dir

    def at_corner(self):
        return self.x % TILE == 0 and self.y % TILE == 0

    def tile(self):
        return (self.x // TILE, self.y // TILE)

    def _update_house(self):
        """Bob vertically inside the house until the release frame."""
        ny = self.y + self.bob_dir
        if ny < HOUSE_BOB_MIN or ny > HOUSE_BOB_MAX:
            self.bob_dir *= -1
            ny = self.y + self.bob_dir
        self.y = ny

    def _update_leaving(self):
        """Rise through the door, then slide onto the grid line.

        The door center (x=54) is mid-tile, off the 4 px grid, so the
        ghost must slide to a grid line before the AI can pick edges.
        """
        if self.y > HOUSE_EXIT_Y:
            self.y -= 1
        elif self.x > HOUSE_EXIT_X:
            self.x -= 1
        else:
            # on a grid corner of the open row; AI takes over
            # (dir still UP, so the edge back down into the house is excluded)
            self.state = OUTSIDE

    def _target_tile(self, game):
        """The tile this ghost type aims for."""
        pt = game.pacman_tile()
        if self.kind == BLINKY:
            return pt
        if self.kind == PINKY:
            d = game.pacman.dir
            if d is None:
                return pt
            return (pt[0] + 4 * d[0], pt[1] + 4 * d[1])
        if self.kind == INKY:
            b = game.ghost_tile(BLINKY)
            return (2 * pt[0] - b[0], 2 * pt[1] - b[1])
        # CLYDE: chase when far (>8 tiles), flee to a far corner near
        if _manhattan(self.tile(), pt) > 8:
            return pt
        return min(CORNER_TILES,
                   key=lambda c: -_manhattan(c, pt))

    def _choose_edge(self, game):
        """At a corner: pick the walkable edge (no reversing, no closed
        door) whose tile is closest to the target. Ties break by
        up > left > right > down, like the arcade."""
        target = self._target_tile(game)
        reverse = (-self.dir[0], -self.dir[1])
        best = None
        best_key = None
        for d in EDGE_PRIORITY:
            if d == reverse:
                continue
            tc = ((self.x + d[0] * TILE) // TILE,
                  (self.y + d[1] * TILE) // TILE)
            if not maze.is_walkable(tc[0], tc[1]):
                continue
            if maze.tile_at(tc[0], tc[1]) == "-":
                continue  # the house door stays closed for roamers
            key = (_manhattan(tc, target), EDGE_PRIORITY.index(d))
            if best_key is None or key < best_key:
                best_key, best = key, d
        return best if best is not None else self.dir

    def _update_outside(self, game):
        if self.at_corner():
            self.dir = self._choose_edge(game)
        nx = self.x + self.dir[0] * GHOST_SPEED
        ny = self.y + self.dir[1] * GHOST_SPEED
        if ny // TILE == TUNNEL_ROW:
            if nx < 0:
                nx += maze.MAZE_PIXEL_W
            elif nx >= maze.MAZE_PIXEL_W:
                nx -= maze.MAZE_PIXEL_W
        if maze.is_walkable(nx // TILE, ny // TILE):
            self.x, self.y = nx, ny

    def update(self, game):
        if self.state == IN_HOUSE:
            if game.frame >= self.release_frame:
                self.state = LEAVING
            else:
                self._update_house()
        elif self.state == LEAVING:
            self._update_leaving()
        else:
            self._update_outside(game)
