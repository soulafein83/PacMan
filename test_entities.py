"""Unit tests for entities.py (pure logic, no pyxel needed)."""
import maze

import entities


def P(x, y=entities.START_Y):
    return entities.Pacman(x, y)


def run(p, frames, desired=None):
    for _ in range(frames):
        p.update(desired)


def run_until(p, cond, max_frames=200):
    for _ in range(max_frames):
        if cond():
            return
        p.update()
    raise AssertionError("condition not met")


def test_starts_waiting_until_a_direction_is_given():
    p = P(entities.START_X)
    run(p, 10)
    assert (p.x, p.y) == (entities.START_X, entities.START_Y)
    p.update("right")
    assert p.dir == entities.RIGHT
    assert p.x == entities.START_X + 1  # moves on the very first frame


def test_moves_one_pixel_per_frame_and_reaches_corners():
    p = P(entities.START_X)
    p.update("right")
    run(p, 3)
    assert p.x == entities.START_X + 4
    assert p.at_intersection()


def test_stops_at_wall():
    # tile (1,1) moving up: tile (1,0) is wall (row 0 is all walls)
    p = P(1 * maze.TILE_SIZE, 1 * maze.TILE_SIZE)
    p.update("up")
    assert p.dir is None  # can't even start facing a wall
    run(p, 10)
    assert (p.x, p.y) == (1 * maze.TILE_SIZE, 1 * maze.TILE_SIZE)
    assert p.at_intersection()


def test_buffered_direction_held_until_a_walkable_intersection():
    # row 6 corridor, heading right. "Up" is a wall at the mid-tile
    # tiles and at corners x=8/12/16 (row 5 cols 1-4 are walls), but
    # open at corner (20, 24) — row 5 col 5 is a dot.
    p = P(4, 24)
    p.update("right")       # x=5, mid-tile
    p.update("up")          # wall above: queued, not taken
    assert p.dir == entities.RIGHT
    run_until(p, lambda: p.at_intersection() and p.dir == entities.UP)
    assert p.x == 20        # turned at corner (20, 24)
    assert p.y < 24         # and is now heading up


def test_mid_tile_turn_is_perpendicular_only():
    # going right, buffering "right" again mid-tile keeps going right
    p = P(4, 4)
    p.update("right")
    p.update("right")       # mid-tile, same axis: ignored
    assert p.dir == entities.RIGHT
    run(p, 1)
    assert p.y == 4


def test_reverse_only_at_intersection():
    p = P(4, 4)
    p.update("right")
    p.update("left")        # mid-tile reverse: ignored
    assert p.dir == entities.RIGHT
    run_until(p, p.at_intersection)
    assert p.x == 8         # reached corner (8, 4)
    p.update("left")        # at intersection: reverse works — and moves
    assert p.dir == entities.LEFT
    assert p.x == 7


def test_tunnel_wraps_left_to_right():
    # tile (0,18) is open (tunnel mouth); moving left wraps to the right
    p = P(0, maze.TUNNEL_ROW * maze.TILE_SIZE)
    p.update("left")
    assert p.x == maze.MAZE_PIXEL_W - 1  # wrapped on the very first step


def test_tunnel_wraps_right_to_left():
    p = P(maze.MAZE_PIXEL_W - 1, maze.TUNNEL_ROW * maze.TILE_SIZE)
    p.update("right")
    assert p.x == 0


def test_no_wrap_outside_tunnel_row():
    # row 19 is open across but has walls at the edges: no wrap allowed
    p = P(8, 19 * maze.TILE_SIZE)
    p.update("left")
    run(p, 10)
    assert p.x == 4  # stopped at the wall (corner), never wrapped


def test_cannot_leave_the_maze_from_the_top():
    p = P(4, 4)
    p.update("down")        # walk down the open column (frame 1: y=5)
    run_until(p, p.at_intersection)
    assert p.y == 8         # corner (4, 8)
    p.update("up")          # reverse at the intersection (moves to y=7)
    assert p.dir == entities.UP
    run(p, 4)
    assert p.y == 4  # stopped at the top wall of row 1 (tile (1,0) is #)


def G(col, row=None):
    """A fresh Game with pacman placed at the corner of tile (col, row)
    (row defaults to the spawn row 11)."""
    g = entities.Game()
    y = entities.START_Y if row is None else row * maze.TILE_SIZE
    g.pacman = entities.Pacman(col * maze.TILE_SIZE, y)
    return g


def test_game_starts_with_every_pellet_from_the_map():
    g = entities.Game()
    expected = {(c, r) for r in range(maze.MAZE_HEIGHT)
                for c in range(maze.MAZE_WIDTH)
                if maze.tile_at(c, r) in (".", "o")}
    expected.discard((entities.START_X // entities.TILE,
                      entities.START_Y // entities.TILE))  # no spawn pellet
    assert g.pellets == expected
    assert g.score == 0
    assert g.maze_empty() is False


def test_sitting_on_a_pellet_eats_it():
    g = G(1, 1)  # tile (1,1) is "."
    g.update()
    assert (1, 1) not in g.pellets
    assert g.score == entities.PELLET_SCORE


def test_power_pellet_is_eaten_and_scores():
    g = G(1, 4)  # tile (1,4) is "o"
    g.update()
    assert (1, 4) not in g.pellets
    assert g.score == entities.PELLET_SCORE


def test_walking_eats_a_trail_of_pellets():
    g = G(13, 11)  # spawn corner, row 11 cols 14-16 are "." (13 has none)
    g.pacman.update("right")
    for _ in range(8):
        g.update()
    assert (14, 11) not in g.pellets
    assert (15, 11) not in g.pellets
    assert (16, 11) in g.pellets  # not reached yet
    assert g.score == 2 * entities.PELLET_SCORE


def test_maze_empty_condition():
    g = entities.Game()
    assert g.maze_empty() is False
    g.pellets.clear()
    assert g.maze_empty() is True
