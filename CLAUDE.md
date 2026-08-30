# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project is

**Planet Protectors** is a father-daughter game. Pina, a blob, defends seven coloured
planets from invading animals, fighting a giant animal boss on each. Mouse only, published
to itch.io as a browser game.

It is built to be read by someone learning game development, so it deliberately follows the
conventions of `resgroup/wind-up` and `resgroup/hill-of-towie-open-source-analysis`.

## Comments and docstrings

**Inside `src/`, keep them succinct.** State what the code does and how to use it. Do not
narrate observations made while developing it, justify design decisions, cite what was
tried, or explain what a bug was. A docstring that argues for a choice is too long. Err far
shorter than instinct.

**In `tests/` and driving scripts (`scripts/`), they can be more verbose.** These are where
a longer explanation earns its place — spelling out what a test pins down, or why a build
step exists at all.

The *why* — reasoning, alternatives considered, findings from debugging — lives in
`docs/superpowers/specs/`, not in source.

## Code map

- **`src/planet_protectors/`** — the game.
  - `bossfight.py` — the `BossFight` state machine. Imports no pygame and reads no clock;
    `tick(dt)` takes the time step from its caller, so a whole fight can be played out in a
    test without a window.
  - `app.py` — the pygame window: draws the fight, routes mouse clicks.
  - `tuning.py` — every number worth changing during a playtest.
- **`tests/`** — mirrors the package layout.
- **`scripts/build_web.py`** — stages and builds the browser version.
- **`docs/superpowers/specs/`** — designs and the reasoning behind them.
- **`docs/game-plan.md`** — the original plan. Still describes Ren'Py; superseded.
- **`docs/extra_docs/`** — private working material, intentionally untracked.

## Commands

This project uses `uv` and `poe` (poethepoet):

- `poe lint` — `ruff format`, `ruff check --fix`, `mypy`, `deptry`. (`poe lint-check` is the
  non-mutating version.)
- `poe test` — pytest under coverage.
- `poe all` — lint + test; the pre-push gate.
- `poe web` — build the browser version and serve it at http://localhost:8000.
- `poe web-build` — build the browser version without serving.

Style: `ruff` with `line-length = 120` and `select = ["ALL"]`; `mypy` is enforced. Match the
surrounding code.

**Keyword arguments.** Pass an argument positionally only when it is really obvious what it
is and what the correct order is — in practice no more than 2 positional args, usually 1,
sometimes 0. Put a `*` in the signature so the rest are keyword-only.

## The browser build

`main.py` must import every third-party module the game uses, including ones it does not use
itself. pygbag parses `main.py` alone to decide which WASM modules to fetch; anything
imported only inside the package is never loaded, and the game renders a blank canvas with
nothing in the browser console. `check_preloads` in `scripts/build_web.py` fails the build
when this is missed.

Verify a web build by reading the bytes that ship, not a file listing:

```commandline
tar xzO -f build/planet_protectors/build/web/planet_protectors.tar.gz assets/main.py
```

## Ground rules

- **Never perform git write actions.** Do not commit, create branches, push, tag, or open
  PRs. Read-only git (`status`, `log`, `diff`, `show`) is fine.
- **Keep tracked docs minimal.** `docs/` holds the plan and the specs, and little else.
- **`docs/extra_docs/` is intentionally untracked and will stay that way.** It holds
  reference photos, scans of drawings, and other material that is not for publishing. Read
  it for context, but never `git add` it and never copy its contents into tracked files.
  Photos in particular carry EXIF metadata, including location.
