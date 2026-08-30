# Planet Protectors — design

A father-daughter game. Pina, a blob, defends seven coloured planets from invading
animals, fighting a giant animal boss on each. Mouse only, published to itch.io as a
browser game.

This document records the decisions and the reasoning behind them. Source files state
behaviour only; the *why* lives here.

## 1. Engine: pygame-ce, exported with pygbag

The original plan specified Ren'Py. We changed it.

Ren'Py is built for dialogue-led visual novels. Planet Protectors is boss-fight-led:
its core loop is click-to-damage with timed counter-attacks and a dodge window. That is
the part of the game Ren'Py is least suited to, and picking an engine for the part of
the game that is not the point is the wrong trade. Ren'Py also runs `.rpy` files under
its own bundled Python, so `ruff`, `mypy`, `pytest` and `uv` cannot reach the game code
at all — and matching the toolchain of the author's other repositories
(`resgroup/wind-up`, `resgroup/hill-of-towie-open-source-analysis`) is an explicit goal,
because the author is learning game development and needs code they can read.

pygame-ce is plain Python. The whole house toolchain applies, timed mechanics are
natural in a game loop, and `pygbag` exports to a folder that can be dropped onto
itch.io.

Godot was considered and rejected: the best browser export of the three and a visual
editor a child could use directly, but GDScript is not Python and none of the existing
style carries over.

## 2. Structure

```
planet-protectors/
├── main.py                      # pygbag entry point
├── src/planet_protectors/
│   ├── __init__.py
│   ├── tuning.py                # every tweakable number
│   ├── bossfight.py             # the rules — imports no pygame
│   └── app.py                   # pygame render + input loop
├── tests/
│   └── test_bossfight.py
├── pyproject.toml               # uv + poe + ruff(ALL) + mypy + coverage
├── .python-version
├── .github/workflows/ci.yaml
└── README.md
```

Conventions follow `hot_open`: `src/` layout, hatchling build, `ruff` with
`select = ["ALL"]` at `line-length = 120`, enforced `mypy`, `pytest` under `coverage`,
`poe lint` / `poe test` / `poe all`, and CI running `uv sync --frozen` then
`poe lint-check` then `poe test`.

Keyword-argument discipline follows `wind-up`: at most one or two obvious positional
arguments, everything else keyword-only behind a `*`.

## 3. The rules core

`bossfight.py` holds a `BossFight` state machine and imports nothing from pygame. This
separation is what makes the game testable without opening a window.

```python
class FightState(Enum):
    FIGHTING = auto()
    WON = auto()
    LOST = auto()
```

**Time is injected, not read.** `BossFight.tick(dt)` advances all timers from a
caller-supplied delta; the core never reads a clock. The render loop measures each frame
and passes the value in.

The rejected alternative was letting pygame own the timers, leaving the core as damage
arithmetic. The timing *is* the interesting logic — attack intervals, dodge windows, the
pause before a retry — and it is where bugs will live. Injecting `dt` puts all of it
under test: a loop of `tick(0.1)` calls reproduces any timing scenario exactly, with no
window and no flakiness.

Public surface:

- `tick(dt)` — advance timers, resolve expired dodge windows, handle state transitions
- `hit_boss(*, damage=...)` — damage the boss; wins at zero
- `dodge()` — consume an open dodge window; returns whether it landed
- `attack_incoming` — whether a dodge window is currently open

## 4. Failure model: lose, then instant retry

Pina can lose, so winning means something, but the cost is a brief "try again!" beat and
an automatic reset to full health inside the same fight. No game-over screen, no menu,
no lost progress.

The player is seven. A real lose state supplies stakes; an instant, frictionless retry
keeps repeated failure from becoming the reason she puts the game down. `LOST` is
therefore a transient state that `tick` clears itself after a short delay, not one that
waits on input.

## 5. Tuning

Every number a playtest might change — boss and player health, damage per click, seconds
between attacks, dodge window length, retry delay — lives in `tuning.py`. The plan calls
for constant playtesting with the co-creator and free adjustment of difficulty; that is
only practical if the numbers are in one obvious place rather than scattered through the
render code.

## 6. Art

Blobs are drawn as coloured circles. Because the cast genuinely is blob-shaped, these are
close to final art rather than throwaway placeholders, so the game is visually legible
from the first run and hand-drawn or generated art can be dropped in later without
restructuring.

## 7. Web export

`pygbag` requires the main loop be `async` with an `await asyncio.sleep(0)` each frame.
That constraint is contained entirely within `app.py`.

The `src/` layout needs a staging step, and the entry point carries a constraint. Both
were found by testing the export in a browser, and both are handled by
`scripts/build_web.py`.

**Staging.** pygbag bundles every file in the directory holding `main.py`. Run against the
repository root it sweeps up `.venv` and the tool caches, and fails on media files inside
pygame's own test fixtures. The build script stages the entry point and the package into a
clean directory first.

**Preload scanning.** pygbag decides which WASM modules to fetch by parsing `main.py`
alone (`scan_imports`, via `preload_code`). A dependency imported only inside the package
is never fetched; the game then renders a blank canvas, and because pygbag routes Python
output to its own on-page terminal, nothing appears in the browser console. `main.py`
must therefore import every third-party module the game needs, even ones it does not use
itself. `check_preloads` in `scripts/build_web.py` fails the build when one is missing, so
this cannot recur silently as sound and images are added.

Isolating this took a bisection ladder from a working minimal pygbag app to the game, one
change at a time. Worth repeating if the web build ever breaks in a way the console does
not explain: the browser console shows loader activity only, so a colour-coded control app
is a faster signal than log reading.

## 8. First session scope

1. Repo skeleton in house style; `poe all` green
2. Trivial pygame window with a clickable blob
3. `pygbag` export, confirmed running in a browser
4. `BossFight` state machine, built test-first
5. Render layer: health bars, timed attacks, dodge window, win/lose
6. Re-export and confirm the fight still runs in a browser

If step 3 proves difficult, the session stops there and the mechanics follow once the
ground is known to be solid.

## 9. Out of scope for now

Story scenes and dialogue, planet progression beyond a single fight, sound, and the
remaining six planets. `docs/game-plan.md` still describes the Ren'Py approach; it will
be revised once the pygame version has proven itself.
