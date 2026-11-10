# Plan wdrożenia — Pac-Man (Pyxel)

Klasyka arcade z 1980 w Pyxel: labirynt 28×26, 4 duchy z prostą AI,
power-peletki, 3 życia, rosnąca trudność.

## Zasady pracy

- Każda warstwa jest **cienkim, zweryfikowanym krokiem**: po każdym kroku
  gra jest uruchamialna, testy przechodzą, jest commit.
- Logika gry (siatka, ruch, AI) żyje w czystym Pythonie (testowalna
  headless); warstwa pyxel to tylko render + input.
- Każdy krok (po kroku 1) startuje dopiero po potwierdzeniu użytkownika.
- Kolory: indeksy palety 16-kolorowej Pyxel (0–15), nie hex RGB.
- Testy: `pytest test_maze.py test_main.py` (stub pyxel, headless) +
  smoke test na prawdziwym pyxel w trybie `headless=True`.

## Architektura

| Plik | Rola |
|------|------|
| `maze.py` | Mapa labiryntu (28×26, kafelki 4 px), `tile_at`, `is_walkable`, listy pelet — czysty Python, zero pyxel |
| `entities.py` (krok 2+) | Pacman/duchy: pozycje, prędkości, kierunki — czysta logika |
| `main.py` | Warstwa pyxel 3.x: `pyxel.init(..., title=...)`, `pyxel.run(update, draw)`, stany, render |
| `test_maze.py`, `test_entities.py`, `test_main.py` | Testy (stub pyxel = headless, bez OpenGL) |

## Kroki

### 1. Szkielet — DONE ✅ (commit `f98bfae`, fix API `94a2ad7`)

- [x] Projekt: venv, `requirements.txt` (pyxel>=3.0), git, README
- [x] `maze.py`: mapa 28×26 (112×104 px, offset OX=24, OY=20), 426 klatek
      przejściowych (spójne — flood fill), 412 pelet, 4 power-peletki,
      drzwi domu duchów (13,12)/(14,12)
- [x] `main.py` na API **pyxel 3.0**: `init(width, height, title=...)`,
      `run(update, draw)`, `cls`, `btnp`, `frame_count` (atrybut),
      kolory = indeksy palety 0–15
- [x] Ekran tytułu (tytuł + migający "PRESS ENTER"), menu ↔ gra
      (Enter / Esc)
- [x] Testy: 5 testów logiki labiryntu + 5 testów warstwy render (stub)
- [x] Smoke test headless: 60 klatek na prawdziwym pyxel 3.0.1
- [x] Repo GitHub: `soulafein83/PacMan` (public)

### 2. Ruch pacmana — DONE ✅

- [x] Klasa `Pacman` w `entities.py`: pozycja pikselowa (4-px siatka,
      1 px/frame), kierunek, pozycja startowa (52, 44)
- [x] Ruch po siatce: płynny 1 px/frame, decyzje na skrzyżowaniach
      (oba współrzędne % 4 == 0)
- [x] Bufor kierunku: wciśnięcie strzałki jest pamiętane (`queued`) i
      stosowane przy najbliższym skrzyżowaniu (klasyczne zachowanie)
- [x] Obrót w lewo/prawo dozwolony również na prostej (oś prostopadła);
      zawracanie tylko na skrzyżowaniu
- [x] Tunel w rzędzie 18: otwarte krawędzie + wrap-around (bez karnego
      zwolnienia — pozostawione opcjonalnie)
- [x] Render pacmana: 4×4 px kwadrat (kolor 13), kierunek wizualny
      na później (krok 8)
- [x] Testy: 10 testów w `test_entities.py` (ruch, bufor, obrót,
      zawracanie, tunel w obie strony, brak wrapu poza tunelem, ściany)
      + 2 testy warstwy pyxel w `test_main.py` (render + ruch przy
      trzymanym strzałce)
- [x] Poprawka mapy: power-peletki spójne (4× `o`), 8× `O` → `.`
      (poprzednio `O` było nieprzejściwalne — ściana w rogach)

### 3. Peletki + score + HUD — DONE ✅

- [x] Klasa `Game` w `entities.py`: `pellets` jako zbiór (col,row),
      `score`, `maze_empty()`; zjadanie peletki kafelka pod pacmanem
      (+10 pkt). Kafelek spawnu (13,11) bez peletki (jak w oryginale —
      brak darmowych punktów na starcie)
- [x] Score: +10 za peletę, HUD na górze (SCORE, HIGH SCORE) — font
      Pyxel 8×8, dwie linijki (etykiety y=2, wartości y=10) powyżej
      labiryntu (OY=20)
- [x] High score trwały w sesji (moduł `main`, przez menu ↔ gra;
      plik na później, opcjonalnie)
- [x] Warunek: labirynt pusty → `maze_empty()` (mechanika przejścia
      w kroku 6)
- [x] Render: `draw_maze` rysuje tylko peletki ze zbioru `game.pellets`
- [x] Testy: 5 nowych w `test_entities.py` (zbiór zgodny z mapą,
      zjadanie na miejscu / power / w ruchu, `maze_empty`) +
      4 nowych w `test_main.py` (HUD score/high, score rośnie w HUD,
      brak rysowania zjedzonych pelet) + 2 poprawione (stan gry w
      `main.game`)
- [x] Smoke test headless na prawdziwym pyxel: `smoke_test.py`
      (120 klatek; `pyxel.quit()` wychodzi bez flush stdout — dlatego
      print z flush przed quit)

### 4. Dom duchów + wypuszczanie + AI

- [ ] `Ghost` w `entities.py`: pozycja, kierunek, prędkość, typ
      (Blinky/Pinky/Inky/Clyde), stan (w domie / na zewnątrz /
      ucieka)
- [ ] Dom duchów: 4 duchy startują w domu (rzędy 11–13, kolumny 12–15),
      drzwi (13,12)/(14,12); sekwencja wypuszczania (co X sekund
      jeden duch)
- [ ] AI na kafelkach (decyzje na skrzyżowaniu, nie na pikselach):
      - Blinky: goni pacmana (target = kafelek pacmana)
      - Pinky: celuje 4 kafeleki przed pacmanem (wektor)
      - Inky: 2×(2×pacman − blinky) uproszczony
      - Clyde: goni pacmana, jeśli daleko (>8), inaczej ucieka
    - wybór krawędzi skrzyżowania minimalizującej odległość do
      celu (bez cofania w krawędź, z której duch wszedł)
- [ ] Kolory duchów (B=niebieski, P=pink, I=cyjan, C=bordo)
- [ ] Testy: duch nie wchodzi w ścianę, wybór krawędzi = min odległość,
      sekwencja wypuszczania, cele typów (Pinky = pacman + 4×dir)

### 5. Power-peletki + frightened + jedzenie duchów

- [ ] Power-peletki: 4 duże (pozycje z mapy), zjedzenie → duchy
      `frightened` na czas (np. 6 s, malejący z poziomem), duchy
      wolniej (~połowa prędkości), kolor → biały/błędny
- [ ] Fleeing: duchy wybierają krawędź **maksymalizującą** odległość
      do pacmana
- [ ] Jedzenie ducha: punkty 200/400/800/1600 (kumulacja), duch
      wraca do domu (bez ciała), odrodzenie po czasie
- [ ] Blinking na ostatnich 2 s frightened (alternacja kolorów)
- [ ] Testy: timer frightened, punktacja kumulacyjna, cel fleeing,
      powrót do domu, odrodzenie

### 6. Życia, śmierć, game over, poziomy

- [ ] 3 życia (ikony pod HUD / pod labiryntem), kolizja z duchem
      (radyus < 4 px) → śmierć: animacja pacmana, utrata życia
- [ ] Respawn pacmana w strefie startu (13.5, 11); duchy wracają do
      domu (lub reset pozycji, uproszczenie)
- [ ] Game over przy 0 żyć: ekran, score, Enter → menu / restart
- [ ] Poziom: po opróżnieniu labiryntu — reset pelet, +1 poziom,
      prędkość +X%, czas frightened −Y s
- [ ] Pauza (Esc w grze → powrót do menu już istnieje; opcjonalnie P)
- [ ] Testy: utrata życia, game over, respawn, przejście poziomu
      (prędkość rośnie, pelety zresetowane)

### 7. Audio: BGM + SFX

- [ ] `pyxel.init_sound(...)` / `sound_bank`: BGM (prosty loop w stylu
      "Pac-Man march"), SFX: peletka (krótkie "chomp"), power,
      jedzenie ducha, śmierć, start poziomu
- [ ] Ewentualnie `pyxel.play_sequencer` dla prostych sekwencji;
      fallback: pojedyncze SFX bez BGM, jeśli nie zdążymy
- [ ] Wyciszenie z menu / pauza w game over
- [ ] Test headless: init audio nie blokujący (audio init nieudany
      = nie-fatal)

### 8. Wykończenie

- [ ] Animacje: rotacja/ustawienie kierunku pacmana (sprite 2×2
      kadry), śmierć (sekwencja klatek), duchy z oczami wskazującymi
      kierunek
- [ ] Balans: prędkości, czasy frightened, sekwencja duchów
      vs oryginał (tolerancja retro)
- [ ] Kontrolki: czytelny HUD (score/high/score/lives/level),
      ekran startu poziomu (poziom 1, 2, ...)
- [ ] README: pełna dokumentacja (sterowanie, struktura, testy),
      screeny/animacja (GIF)
- [ ] Ostatni przegląd kodu (review) + commit tag `v1.0`

## Definicja gotowości kroku

Krok = gotowy, gdy: (1) wszystkie testy przechodzą, (2) smoke test
headless na prawdziwym pyxel, (3) użytkownik potwierdza działanie
na swoim ekranie, (4) commit z opisem kroku.
