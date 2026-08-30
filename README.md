# Planet Protectors

Pina, a blob, defends seven coloured planets from invading animals. Each planet ends in a
boss fight against a giant version of the animals invading it.

A father-daughter game, playable with the mouse alone, built to run in a browser.

## Quickstart

The environment is created and managed using [uv](https://docs.astral.sh/uv/):

```commandline
uv sync
```

To play the desktop version:

```commandline
uv run main.py
```

To run formatting, linting and tests:

```commandline
uv run poe all
```

## Browser version

The game is published to [itch.io](https://itch.io) as a browser build, produced with
[pygbag](https://pypi.org/project/pygbag/):

```commandline
uv sync --group web
uv run poe web
```

This serves the game at http://localhost:8000 and writes the uploadable build to
`build/planet_protectors/build/web`. Use `poe web-build` to build without serving.

**`main.py` must import every third-party module the game uses**, including ones it does
not use itself, because pygbag reads `main.py` alone to decide which WASM modules to fetch
into the browser. A module imported only inside `src/planet_protectors/` is never loaded
and the game shows a blank canvas with nothing in the browser console. The build fails with
an explanatory message if this is missed, so adding sound or images means adding the import
to `main.py` too.

## How the code is laid out

Game rules live in `src/planet_protectors/bossfight.py` and import nothing from pygame,
so they can be tested without opening a window. `src/planet_protectors/app.py` draws the
state and feeds mouse clicks back in. Every number worth tweaking during a playtest is in
`src/planet_protectors/tuning.py`.

The design and the reasoning behind it are in
`docs/superpowers/specs/2026-08-30-planet-protectors-design.md`.
