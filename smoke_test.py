"""Headless smoke test with real pyxel: 120 frames of play.

pyxel 3.0's run() has no frame limit and pyxel.quit() exits the
process without flushing stdout, so the loop is driven by hand and
the result is printed with an explicit flush before quit.

Run:  .venv/bin/python smoke_test.py
"""
import sys

import pyxel

import entities
import main


def main_smoke():
    pyxel.init(main.SCREEN_W, main.SCREEN_H, headless=True,
               title="Pac-Man (Pyxel) — smoke")
    main.state = main.STATE_PLAY
    main.game = entities.Game()
    pellets_before = len(main.game.pellets)
    for _ in range(120):
        main.pyxel.frame_count += 1
        main.update()  # no buttons pressed headless; still advances
        main.draw()
    print("smoke OK — 120 frames, pellets: %d, score: %d"
          % (pellets_before, main.game.score), flush=True)
    pyxel.quit()


if __name__ == "__main__":
    main_smoke()
