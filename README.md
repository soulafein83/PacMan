# Pac-Man (Pyxel)

Klasyka arcade z 1980 w Pyxel: labirynt 28×26, 4 duchy z prostą AI,
power-peletki, 3 życia, rosnąca trudność.

## Uruchomienie

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Uwaga: gra potrzebuje sesji graficznej (X11/Wayland). Na headless
uruchamiaj testy:

```bash
.venv/bin/python -m pytest test_maze.py test_main.py -v
```

## Sterowanie

| Klawisz   | Działanie        |
|-----------|------------------|
| strzałki  | ruch (krok 2)    |
| Enter     | start / przejścia |
| Esc       | powrót do menu   |

## Status wdrożenia (kroki z planu)

- [x] 1. Szkielet: init pyxel, statyczny labirynt, ekran tytułu
- [ ] 2. Ruch pacmana (siatka + interpolacja, bufor kierunku, tunel)
- [ ] 3. Peletki + score + HUD
- [ ] 4. Dom duchów + wypuszczanie + uproszczona AI
- [ ] 5. Power-peletki, frightened, jedzenie duchów
- [ ] 6. Życia, śmierć, game over, poziomy
- [ ] 7. Audio: BGM + SFX
- [ ] 8. Wykończenie: balans, README, kontrolki

## Struktura

- `maze.py` — definicja labiryntu + pomocnicze funkcje kafelków (czysty Python)
- `main.py` — warstwa pyxel: pętla gry, stany, render
- `test_maze.py` / `test_main.py` — testy (logika + smoke test headless)
