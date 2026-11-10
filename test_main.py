"""Headless tests for main.py using a stub pyxel module (no OpenGL needed).

The stub mirrors the pyxel 3.0 API used by main.py: pyxel.init,
pyxel.run(update, draw), pyxel.cls, pyxel.rect, pyxel.text, pyxel.btnp,
pyxel.KEY_*, pyxel.frame_count. It records draw calls and lets tests
simulate button presses.
"""
import sys
import types

import maze


def _make_stub():
    stub = types.ModuleType("pyxel")
    stub.calls = []
    stub.KEY_RETURN = 28
    stub.KEY_ESCAPE = 53
    stub.KEY_LEFT = 100
    stub.KEY_RIGHT = 101
    stub.KEY_UP = 102
    stub.KEY_DOWN = 103
    stub.frame_count = 0
    stub._pressed = set()
    stub._held = set()

    def init(*a, **k):
        pass

    def quit():
        pass

    def run(update, draw):
        pass

    def cls(color=0):
        stub.calls.append(("cls", color))

    def rect(x, y, w, h, color):
        stub.calls.append(("rect", x, y, w, h, color))

    def text(x, y, s, color):
        stub.calls.append(("text", x, y, s, color))

    def btnp(key, hold=0, repeat=0):
        was_pressed = key in stub._pressed
        stub._pressed.discard(key)
        return was_pressed

    def btn(key):
        return key in stub._held

    for name in ("init", "quit", "run", "cls", "rect", "text", "btnp", "btn"):
        setattr(stub, name, locals()[name])
    return stub


# Register the stub BEFORE importing main (main does `import pyxel`).
sys.modules["pyxel"] = _make_stub()

import main  # noqa: E402


def _reset(pressed=(), held=(), game=None, high=0):
    main.pyxel.calls.clear()
    main.pyxel._pressed = set(pressed)
    main.pyxel._held = set(held)
    if game is not None:
        main.game = game
    main.HIGH_SCORE = high


def test_maze_render_draws_every_tile():
    _reset(game=main.entities.Game())
    main.draw_maze()
    rects = [c for c in main.pyxel.calls if c[0] == "rect"]
    walls = sum(row.count("#") for row in maze.MAZE_MAP)
    pellets = sum(row.count(".") for row in maze.MAZE_MAP)
    powers = sum(row.count("o") for row in maze.MAZE_MAP)
    doors = sum(row.count("-") for row in maze.MAZE_MAP)
    # minus one: the spawn tile's pellet is never drawn (no spawn pellet)
    assert len(rects) == walls + pellets + powers + doors - 1
    # every rect stays inside the maze pixel bounds (offset by OX/OY)
    for _, x, y, w, h, _ in rects:
        assert main.OX <= x and x + w <= main.OX + maze.MAZE_PIXEL_W
        assert main.OY <= y and y + h <= main.OY + maze.MAZE_PIXEL_H


def test_menu_draws_title():
    _reset()
    main.state = main.STATE_MENU
    main.pyxel.frame_count = 0
    main.draw_menu()
    texts = [c[3] for c in main.pyxel.calls if c[0] == "text"]
    assert "PAC-MAN" in texts
    assert "PRESS ENTER" in texts


def test_enter_switches_menu_to_play():
    _reset(pressed=[main.pyxel.KEY_RETURN])
    main.state = main.STATE_MENU
    main.update()
    assert main.state == main.STATE_PLAY


def test_escape_switches_play_to_menu():
    _reset(pressed=[main.pyxel.KEY_ESCAPE])
    main.state = main.STATE_PLAY
    main.update()
    assert main.state == main.STATE_MENU


def test_play_draws_maze_and_pacman():
    _reset(game=main.entities.Game())
    main.state = main.STATE_PLAY
    main.draw()
    assert any(c[0] == "rect" for c in main.pyxel.calls)
    assert not any(c[0] == "text" and c[3] == "PAC-MAN"
                   for c in main.pyxel.calls)
    # pacman square: 4x4 at its maze position (offset by OX/OY)
    p = main.game.pacman
    assert ("rect", main.OX + p.x, main.OY + p.y, 4, 4, 13) in main.pyxel.calls


def test_holding_an_arrow_moves_pacman_in_play():
    _reset(held=[main.pyxel.KEY_RIGHT], game=main.entities.Game())
    main.state = main.STATE_PLAY
    for _ in range(5):
        main.update()
    assert main.game.pacman.x == main.entities.START_X + 5
    assert main.game.pacman.y == main.entities.START_Y


def test_hud_draws_score_and_high_score():
    _reset(game=main.entities.Game(), high=410)
    main.state = main.STATE_PLAY
    main.draw()
    texts = [c[3] for c in main.pyxel.calls if c[0] == "text"]
    assert "SCORE" in texts
    assert "HIGH SCORE" in texts
    assert "0000" in texts   # fresh round score
    assert "0410" in texts   # session high


def test_hud_shows_score_after_eating_pellets():
    # pacman walks right from the spawn tile through (14,11),(15,11);
    # the spawn tile itself has no pellet
    _reset(held=[main.pyxel.KEY_RIGHT], game=main.entities.Game())
    main.state = main.STATE_PLAY
    for _ in range(9):
        main.update()
    assert main.game.score == 20
    main.pyxel.calls.clear()
    main.draw()
    texts = [c[3] for c in main.pyxel.calls if c[0] == "text"]
    assert "0020" in texts
    assert main.HIGH_SCORE == 20  # session high follows the round


def test_draw_maze_skips_spawn_and_eaten_pellets():
    _reset(held=[main.pyxel.KEY_RIGHT], game=main.entities.Game())
    main.state = main.STATE_PLAY
    main.pyxel.calls.clear()
    main.draw_maze()
    rects = [c for c in main.pyxel.calls if c[0] == "rect"]
    total = sum(row.count(c) for row in maze.MAZE_MAP for c in "#.-o")
    assert len(rects) == total - 1  # spawn tile's pellet is never drawn
    for _ in range(4):
        main.update()  # eats the next pellet, tile (14,11)
    main.pyxel.calls.clear()
    main.draw_maze()
    rects = [c for c in main.pyxel.calls if c[0] == "rect"]
    assert len(rects) == total - 2
