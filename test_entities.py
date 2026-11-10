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


# --- step 4: ghost house, release sequence, tile-based AI ---------------

def gh(g, kind):
    return next(x for x in g.ghosts if x.kind == kind)


def test_ghosts_start_in_the_house():
    g = entities.Game()
    assert [x.kind for x in g.ghosts] == list(entities.GHOST_KINDS)
    for i, x in enumerate(g.ghosts):
        assert x.state == entities.IN_HOUSE
        assert x.release_frame == entities.Game.RELEASE_STAGGER_FRAMES[i]
        assert x.x == entities.HOUSE_X
        assert x.y // entities.TILE == 13  # interior row of the house


def test_release_sequence_is_staggered():
    g = entities.Game()
    g.update()
    assert gh(g, entities.BLINKY).state == entities.LEAVING
    for k in (entities.INKY, entities.PINKY, entities.CLYDE):
        assert gh(g, k).state == entities.IN_HOUSE
    run_game(g, 11)   # frame 12
    assert gh(g, entities.BLINKY).state == entities.OUTSIDE
    run_game(g, 168)  # frame 180
    assert gh(g, entities.INKY).state == entities.LEAVING
    assert gh(g, entities.CLYDE).state == entities.IN_HOUSE
    run_game(g, 12)   # frame 192
    assert gh(g, entities.INKY).state == entities.OUTSIDE
    run_game(g, 168)  # frame 360
    assert gh(g, entities.PINKY).state == entities.LEAVING
    run_game(g, 12)   # frame 372
    assert gh(g, entities.PINKY).state == entities.OUTSIDE
    assert gh(g, entities.CLYDE).state == entities.IN_HOUSE
    run_game(g, 168)  # frame 540
    assert gh(g, entities.CLYDE).state == entities.LEAVING
    run_game(g, 12)   # frame 552
    assert gh(g, entities.CLYDE).state == entities.OUTSIDE


def run_game(g, frames):
    for _ in range(frames):
        g.update()


def test_ghosts_never_enter_walls():
    g = entities.Game()
    for _ in range(600):
        g.update()
        for x in g.ghosts:
            if x.state == entities.OUTSIDE:
                assert maze.is_walkable(*x.tile())


def _corner_ghost(kind, x, y, d):
    g = entities.Ghost(kind, x, y)
    g.state = entities.OUTSIDE
    g.dir = d
    return g


def test_edge_choice_minimizes_distance_to_target():
    g = G(1, 10)  # pacman tile (1,10)
    x = _corner_ghost(entities.BLINKY, 48, 40, entities.UP)
    # LEFT -> tile (11,10), dist 10; UP/RIGHT -> dist 12 each
    assert x._choose_edge(g) == entities.LEFT


def test_edge_tie_breaks_by_priority_up_first():
    g = G(11, 9)  # pacman tile (11,9)
    x = _corner_ghost(entities.BLINKY, 48, 40, entities.UP)
    # UP -> (12,9) dist 1, LEFT -> (11,10) dist 1: up wins the tie
    assert x._choose_edge(g) == entities.UP


def test_ghost_never_reverses():
    g = G(15, 11)  # pacman tile (15,11)
    x = _corner_ghost(entities.BLINKY, 52, 44, entities.LEFT)
    # RIGHT (dist 1) is the reverse -> excluded; DOWN is the door;
    # UP -> (13,10) and LEFT -> (12,11) both dist 3: up wins
    assert x._choose_edge(g) == entities.UP


def test_pinky_targets_four_tiles_ahead_of_pacman():
    g = G(1, 11)  # pacman tile (1,11)
    g.pacman.dir = entities.RIGHT
    assert gh(g, entities.PINKY)._target_tile(g) == (5, 11)


def test_pinky_targets_pacman_tile_without_a_direction():
    g = G(1, 11)
    assert gh(g, entities.PINKY)._target_tile(g) == (1, 11)


def test_blinky_targets_pacman_tile():
    g = G(4, 4)
    assert gh(g, entities.BLINKY)._target_tile(g) == (4, 4)


def test_inky_target_is_double_pacman_minus_blinky():
    g = G(1, 11)  # fresh game: blinky at px (54,52) -> tile (13,13)
    assert gh(g, entities.BLINKY).tile() == (13, 13)
    # 2*(1,11) - (13,13) = (-11, 9)
    assert gh(g, entities.INKY)._target_tile(g) == (-11, 9)


def test_clyde_chases_when_far():
    g = G(1, 11)  # clyde at tile (13,13): manhattan 14 > 8
    assert gh(g, entities.CLYDE)._target_tile(g) == (1, 11)


def test_clyde_flees_to_the_far_corner_when_near():
    g = G(1, 11)
    c = gh(g, entities.CLYDE)
    c.x, c.y = 7 * entities.TILE, 10 * entities.TILE  # tile (7,10), dist 7
    assert c._target_tile(g) == (26, 24)


def test_pacman_cannot_enter_the_ghost_house_door():
    p = entities.Pacman(entities.START_X, entities.START_Y)
    for _ in range(20):
        p.update("down")
    assert p.y == entities.START_Y + 3  # stopped at the bottom of row 11
    assert p.y // entities.TILE == 11
