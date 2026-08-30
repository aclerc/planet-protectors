"""Every number a playtest might want to change.

Adjust these freely while playing. Nothing here affects how the game works, only how it
looks and how hard it feels.
"""

from dataclasses import dataclass

Colour = tuple[int, int, int]
Point = tuple[int, int]


@dataclass(frozen=True)
class Tuning:
    """Tweakable game values."""

    boss_max_health: int = 100
    pina_max_health: int = 100
    hit_damage: int = 10
    attack_damage: int = 20

    seconds_between_attacks: float = 3.0
    dodge_window_seconds: float = 2.0
    retry_delay_seconds: float = 2.0

    screen_width: int = 960
    screen_height: int = 540
    frames_per_second: int = 60

    space_colour: Colour = (18, 16, 40)
    text_colour: Colour = (240, 240, 245)

    pina_colour: Colour = (90, 200, 250)
    pina_radius: int = 45
    pina_centre: Point = (150, 400)

    boss_colour: Colour = (230, 90, 110)
    boss_radius: int = 95
    boss_centre: Point = (560, 220)

    bar_height: int = 26
    bar_margin: int = 40
    boss_bar_top: int = 30
    pina_bar_top: int = 470

    dodge_button_size: Point = (240, 74)
    dodge_button_centre: Point = (480, 380)
    dodge_colour: Colour = (250, 205, 90)


TUNING = Tuning()

PLANET_COLOURS: tuple[Colour, ...] = (
    (250, 120, 120),  # red planet
    (250, 190, 100),  # orange planet
    (250, 240, 120),  # yellow planet
    (140, 220, 140),  # green planet
    (120, 180, 250),  # blue planet
    (180, 140, 240),  # purple planet
    (245, 160, 220),  # pink planet
)
