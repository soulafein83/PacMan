"""Pac-Man in Pyxel.

Step 1: skeleton — pyxel init, static maze rendered from the text map,
title screen. No entities yet (player/ghosts arrive in later steps).

Run:  .venv/bin/python main.py
"""
import pyxel

import maze

SCREEN_W = 160
SCREEN_H = 144

# Center the maze (112 x 104 px); top margin leaves room for the HUD.
OX = (SCREEN_W - maze.MAZE_PIXEL_W) // 2
OY = 20

STATE_MENU = 0
STATE_PLAY = 1

WALL_COLOR = 0x2159ff
PELLET_COLOR = 0xffb8ae
DOOR_COLOR = 0xffb8ae
TITLE_COLOR = 0xffffff
ACCENT_COLOR = 0xffd800

state = STATE_MENU


def draw_maze():
    for row in range(maze.MAZE_HEIGHT):
        line = maze.MAZE_MAP[row]
        for col in range(maze.MAZE_WIDTH):
            ch = line[col]
            x = OX + col * maze.TILE_SIZE
            y = OY + row * maze.TILE_SIZE
            if ch == "#":
                pyxel.rect(x, y, maze.TILE_SIZE, maze.TILE_SIZE, WALL_COLOR)
            elif ch == ".":
                pyxel.rect(x + 1, y + 1, 2, 2, PELLET_COLOR)
            elif ch == "o":
                pyxel.rect(x, y + 1, 4, 2, PELLET_COLOR)
            elif ch == "-":
                pyxel.rect(x, y + 1, maze.TILE_SIZE, 2, DOOR_COLOR)
            # " " = empty floor: leave background


def draw_menu():
    pyxel.text(52, 44, "PAC-MAN", TITLE_COLOR)
    pyxel.text(32, 60, "RETRO ARCADE", ACCENT_COLOR)
    # blinking hint (1 Hz at 60 fps)
    if (pyxel.frame_count() // 30) % 2 == 0:
        pyxel.text(36, 84, "PRESS ENTER", TITLE_COLOR)
    pyxel.text(52, 120, "STEP 1 - STATIC MAZE", 0x888888)


def frame_event(frame):
    """Input handling (called once per frame by pyxel)."""
    global state
    if state == STATE_MENU:
        if pyxel.keyp(pyxel.KEY_RETURN):
            state = STATE_PLAY
    elif state == STATE_PLAY:
        if pyxel.keyp(pyxel.KEY_ESCAPE):
            state = STATE_MENU


def draw_event():
    """Rendering (called once per frame by pyxel)."""
    pyxel.clear(0)
    if state == STATE_MENU:
        draw_menu()
    else:
        draw_maze()


def main():
    pyxel.init(width=SCREEN_W, height=SCREEN_H, caption="Pac-Man (Pyxel)")
    pyxel.frame_event(frame_event)
    pyxel.update(None)
    pyxel.draw(draw_event)
    pyxel.run()


if __name__ == "__main__":
    main()
