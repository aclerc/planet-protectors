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
    hit_damage: int = 1
    attack_damage: int = 2

    seconds_between_attacks: float = 3.0
    dodge_window_seconds: float = 2.0
    retry_delay_seconds: float = 2.0

    screen_width: int = 960
    screen_height: int = 540
    frames_per_second: int = 60

    sky_colour: Colour = (50, 91, 117)
    ground_colour: Colour = (183, 40, 28)
    tree_colour: Colour = (198, 54, 38)
    trunk_colour: Colour = (146, 40, 28)
    bush_colour: Colour = (158, 36, 26)
    ink_colour: Colour = (26, 24, 26)
    text_colour: Colour = (36, 30, 30)
    ground_top: int = 440

    pina_colour: Colour = (204, 46, 32)
    teal_colour: Colour = (22, 140, 146)
    pina_radius: int = 50
    pina_centre: Point = (200, 350)
    pina_speed: float = 300.0
    pina_roam_margin: int = 100  # inset from each side edge that keeps his hands on screen

    boss_colour: Colour = (146, 148, 152)
    boss_shade_colour: Colour = (108, 110, 116)
    boss_radius: int = 95
    boss_centre: Point = (700, 200)
    boss_speed: float = 120.0
    boss_roam_margin: Point = (95, 125)  # inset from each edge that keeps ears and feet on screen

    bar_height: int = 26
    bar_margin: int = 40
    boss_bar_top: int = 30
    pina_bar_top: int = 470
    boss_bar_colour: Colour = (92, 94, 100)
    pina_bar_colour: Colour = (22, 140, 146)

    message_centre: Point = (480, 360)
    label_font_size: int = 56
    message_font_size: int = 40
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
