"""Headless tests for main.py using a stub pyxel module (no OpenGL needed).

The real pyxel requires a GL context (a window), unavailable on this
headless machine. The stub records drawing calls so we can assert what
the render layer would actually draw.
"""
import sys
import types

import maze


def _make_stub():
    stub = types.ModuleType("pyxel")
    stub.calls = []
    stub.KEY_RETURN = 28
    stub.KEY_ESCAPE = 53
    stub.KEY_PRESSED = 1
    stub.KEY_RELEASED = 2
    stub.keys = {}

    def init(*a, **k):
        pass

    def quit():
        pass

    def run():
        pass

    def update(cb):
        pass

    def frame_event(cb):
        pass

    def draw(cb):
        pass

    def clear(color=0):
        stub.calls.append(("clear", color))

    def rect(x, y, w, h, color):
        stub.calls.append(("rect", x, y, w, h, color))

    def text(x, y, s, color):
        stub.calls.append(("text", x, y, s, color))

    def frame_count():
        return 0

    def keyp(key):
        return stub.keys.get(key, 0) == stub.KEY_PRESSED

    for name in ("init", "quit", "run", "update", "frame_event", "draw",
                 "clear", "rect", "text", "frame_count", "keyp"):
        setattr(stub, name, locals()[name])
    return stub


# Register the stub BEFORE importing main (main does `import pyxel`).
sys.modules["pyxel"] = _make_stub()

import main  # noqa: E402


def _reset():
    main.pyxel.calls.clear()
    main.pyxel.keys.clear()


def test_maze_render_draws_every_tile():
    _reset()
    main.draw_maze()
    rects = [c for c in main.pyxel.calls if c[0] == "rect"]
    walls = sum(row.count("#") for row in maze.MAZE_MAP)
    pellets = sum(row.count(".") for row in maze.MAZE_MAP)
    powers = sum(row.count("o") for row in maze.MAZE_MAP)
    doors = sum(row.count("-") for row in maze.MAZE_MAP)
    assert len(rects) == walls + pellets + powers + doors
    # every rect stays inside the maze pixel bounds (offset by OX/OY)
    for _, x, y, w, h, _ in rects:
        assert main.OX <= x and x + w <= main.OX + maze.MAZE_PIXEL_W
        assert main.OY <= y and y + h <= main.OY + maze.MAZE_PIXEL_H


def test_menu_draws_title():
    _reset()
    main.state = main.STATE_MENU
    main.draw_menu()
    texts = [c[3] for c in main.pyxel.calls if c[0] == "text"]
    assert "PAC-MAN" in texts
    assert "PRESS ENTER" in texts


def test_enter_switches_menu_to_play():
    _reset()
    main.state = main.STATE_MENU
    main.pyxel.keys[main.pyxel.KEY_RETURN] = main.pyxel.KEY_PRESSED
    main.frame_event(0)
    assert main.state == main.STATE_PLAY


def test_escape_switches_play_to_menu():
    _reset()
    main.state = main.STATE_PLAY
    main.pyxel.keys[main.pyxel.KEY_ESCAPE] = main.pyxel.KEY_PRESSED
    main.frame_event(0)
    assert main.state == main.STATE_MENU


def test_play_draws_maze_not_menu():
    _reset()
    main.state = main.STATE_PLAY
    main.draw_event()
    assert any(c[0] == "rect" for c in main.pyxel.calls)
    assert not any(c[0] == "text" and c[3] == "PAC-MAN"
                   for c in main.pyxel.calls)
