"""Pac-Man in Pyxel.

Step 1: skeleton — pyxel init, static maze rendered from the text map,
title screen. No entities yet (player/ghosts arrive in later steps).

Run:  .venv/bin/python main.py
"""
import pyxel

import entities
import maze

SCREEN_W = 160
SCREEN_H = 144

# Center the maze (112 x 104 px); top margin leaves room for the HUD.
OX = (SCREEN_W - maze.MAZE_PIXEL_W) // 2
OY = 20

STATE_MENU = 0
STATE_PLAY = 1

# Pyxel colors are 16-color palette indices (0..15), not RGB hex:
# 3=blue, 9=orange, 13=yellow, 15=white, 7=dark gray
WALL_COLOR = 3
PELLET_COLOR = 9
DOOR_COLOR = 9
TITLE_COLOR = 15
ACCENT_COLOR = 13
PACMAN_COLOR = 13

TILE = maze.TILE_SIZE

state = STATE_MENU
pacman = entities.Pacman()

KEY_DIRS = {
    pyxel.KEY_LEFT: "left",
    pyxel.KEY_RIGHT: "right",
    pyxel.KEY_UP: "up",
    pyxel.KEY_DOWN: "down",
}


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
    if (pyxel.frame_count // 30) % 2 == 0:
        pyxel.text(36, 84, "PRESS ENTER", TITLE_COLOR)
    pyxel.text(52, 120, "STEP 1 - STATIC MAZE", 7)


def update():
    """Input handling (called once per frame by pyxel.run)."""
    global state, pacman
    if state == STATE_MENU:
        if pyxel.btnp(pyxel.KEY_RETURN):
            pacman = entities.Pacman()
            state = STATE_PLAY
    elif state == STATE_PLAY:
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            state = STATE_MENU
        desired = None
        for key, name in KEY_DIRS.items():
            if pyxel.btn(key):
                desired = name
                break
        pacman.update(desired)


def draw():
    """Rendering (called once per frame by pyxel.run)."""
    pyxel.cls(0)
    if state == STATE_MENU:
        draw_menu()
    else:
        draw_maze()
        # pacman: 4x4 yellow square at its maze-pixel position
        pyxel.rect(OX + pacman.x, OY + pacman.y, TILE, TILE, PACMAN_COLOR)


def main():
    pyxel.init(SCREEN_W, SCREEN_H, title="Pac-Man (Pyxel)")
    pyxel.run(update, draw)


if __name__ == "__main__":
    main()
