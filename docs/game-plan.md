# Point-and-Click Adventure with Boss Fights — Project Plan

A father-daughter game project. Built in **Ren'Py** (Python-based), designed for a 7-year-old co-creator. Playable with mouse only. Target: browser-playable, published on itch.io.

> **Update (30 Aug 2026):** the engine changed from Ren'Py to **pygame-ce**, exported to the browser
> with pygbag. The sections below still describe the Ren'Py approach and are kept for reference until
> they are rewritten. The current design and the reasoning behind the change are in
> [`superpowers/specs/2026-08-30-planet-protectors-design.md`](superpowers/specs/2026-08-30-planet-protectors-design.md).

---

## 1. Tech Stack

- **Engine:** [Ren'Py](https://www.renpy.org/) — free, open source, Python-based visual novel/adventure engine
- **Language:** Ren'Py script language for story/dialogue/choices (simple, readable); Python for the boss fight logic and any custom mechanics
- **Art:** Backgrounds + character sprites — can be simple drawings (scan/photo crayon art), free asset packs, or AI-generated placeholders while prototyping
- **Sound:** Free sound effects from [freesound.org](https://freesound.org) or [opengameart.org](https://opengameart.org) for punches, victory jingles, etc.
- **Publishing:** Ren'Py's built-in "Build Distributions" → Web (HTML5) export → upload to [itch.io](https://itch.io) (free hosting, drag-and-drop)

---

## 2. Project Structure (Ren'Py default, once installed)

```
game-name/
├── game/
│   ├── script.rpy          # main story script (dialogue, choices, scenes)
│   ├── bossfight.rpy        # boss fight screen + logic
│   ├── images/               # backgrounds, characters, boss art
│   ├── audio/                 # sound effects, music
│   └── gui.rpy               # menu/button styling (optional, later)
├── README.md
└── game-plan.md            # this file
```

---

## 3. Build Order (milestones — get a "win" fast, then expand)

1. **Setup**: Install Ren'Py, run the built-in tutorial/demo together (~30 min)
2. **Story sketch (paper, together)**: Where does the story happen? Who are the characters? Where do the boss fights happen, and who are the bosses? Let her design the bosses — great task for a 7-year-old.
3. **First scene**: One background, one character, one dialogue choice. Get something clickable working end to end.
4. **First boss fight (basic)**: Click-to-damage only, no dodge mechanic yet. Health bar that shrinks. Get the loop working.
5. **Add dodge/timer mechanic**: Boss "attacks back" on a timer; player clicks a dodge/block button in time or loses health.
6. **Polish the fight**: sound effects on punch/hit, a screen shake or flash, a victory scene.
7. **Chain everything together**: Story scenes → boss fight → story continues → next boss, etc.
8. **Playtest constantly with her**, especially fight difficulty and timer speed — kids bounce off things that feel unfair. Adjust freely.
9. **Export & publish**: Build → Web (HTML5), test in browser, upload to itch.io.

---

## 4. Boss Fight Mechanic — Starter Sketch

This is the core mechanic: click the boss to damage it, dodge its counter-attacks in time, win when its health hits zero.

**Concept in plain terms:**
- `boss_health` starts at 100, decreases by ~10 each click
- Every few seconds, the boss "telegraphs" an attack (a warning appears)
- Player has ~2 seconds to click "Dodge" — if they don't, they take damage
- When `boss_health <= 0`, trigger victory and return to the story

**Rough Ren'Py/Python sketch** (Claude Code can flesh this out into a real working screen):

```python
# bossfight.rpy

default boss_health = 100
default player_health = 100
default boss_attack_incoming = False

screen boss_fight():
    tag menu
    add "images/boss.png"

    # Health bars (simple colored bars driven by the numbers above)
    bar value boss_health range 100 xpos 100 ypos 50
    bar value player_health range 100 xpos 100 ypos 550

    if boss_attack_incoming:
        text "Dodge now!" xpos 400 ypos 300

    imagebutton:
        idle "images/boss.png"
        xpos 300 ypos 200
        action [SetVariable("boss_health", boss_health - 10), Play("sound", "audio/punch.wav")]

    if boss_attack_incoming:
        textbutton "Dodge" action SetVariable("boss_attack_incoming", False)

label start_boss_fight:
    $ boss_health = 100
    $ player_health = 100
    call screen boss_fight
    if boss_health <= 0:
        "You defeated the boss!"
    return
```

This is intentionally rough — it's meant to be a starting point to hand to Claude Code, not finished code. The timer for boss attacks, the "telegraph" animation, and win/lose branching will need to be built out properly.

---

## 5. Things to Decide Together Before/During Building

- [x] What is the story about? (setting, main character, goal)
It's about different colour planets, being invaded by animals. The main characeter's goal is to defeat all the invading animals and the boss and then go to the next planet. Each planet has citizens which are not animals, they are blob thingys. The main character is another blob thingy but a different colour.  
- [x] How many boss fights, and who/what are the bosses?
One boss for each planet. There are seven planets. The bosses are giant versions of the animals invading the planets. 
- [x] Art style — hand-drawn (scanned), simple shapes, or placeholder art to swap later?
Computer generated. We can supply hand drawn examples.
- [x] Names for the game and main character
The name for the main character should be Pina. The name of the game should be Planet Protectors.

---

## 6. Resources

- Ren'Py docs: https://www.renpy.org/doc/html/
- Ren'Py quickstart tutorial: https://www.renpy.org/doc/html/quickstart.html
- Free sound effects: https://freesound.org
- Free art/assets: https://opengameart.org
- Publishing: https://itch.io (create account → "Upload new project" → drag in the Web export)

---

## 7. Next Steps for Claude Code

1. `renpy` init a new project matching the structure above
2. Implement `bossfight.rpy` properly: working health bars, attack timer, dodge window, win/lose states
3. Wire up placeholder art/sound so it's playable
4. Build out `script.rpy` with the story sketch once decided
5. Test the Web (HTML5) export early and often — some Python features behave differently in the browser build, so catching issues early saves rework
