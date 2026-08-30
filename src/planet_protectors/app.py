"""The game window: draws the fight and turns mouse clicks into actions.

The loop is `async` because the browser build (pygbag) requires it to yield once a frame.
This module owns everything visual; the rules it draws live in `bossfight`.
"""

import asyncio
import math

import pygame

from planet_protectors.bossfight import BossFight, FightState
from planet_protectors.tuning import TUNING, Colour, Point

BAR_BACKGROUND: Colour = (60, 58, 90)


def is_inside_circle(point: Point, *, centre: Point, radius: int) -> bool:
    """Return whether a point falls within a circle."""
    return math.dist(point, centre) <= radius


def dodge_button_rect() -> pygame.Rect:
    """Return the area the player clicks to dodge an incoming attack."""
    rect = pygame.Rect((0, 0), TUNING.dodge_button_size)
    rect.center = TUNING.dodge_button_centre
    return rect


def draw_health_bar(surface: pygame.Surface, *, top: int, health: int, maximum: int, colour: Colour) -> None:
    """Draw a full-width health bar, filled in proportion to the health remaining."""
    width = TUNING.screen_width - 2 * TUNING.bar_margin
    background = pygame.Rect(TUNING.bar_margin, top, width, TUNING.bar_height)
    pygame.draw.rect(surface, BAR_BACKGROUND, background, border_radius=TUNING.bar_height // 2)

    filled = background.copy()
    filled.width = round(width * health / maximum)
    if filled.width > 0:
        pygame.draw.rect(surface, colour, filled, border_radius=TUNING.bar_height // 2)


def draw_centred_text(surface: pygame.Surface, text: str, *, font: pygame.font.Font, centre: Point) -> None:
    """Draw a line of text centred on a point."""
    rendered = font.render(text, True, TUNING.text_colour)  # noqa: FBT003
    surface.blit(rendered, rendered.get_rect(center=centre))


def draw_fight(surface: pygame.Surface, fight: BossFight, *, font: pygame.font.Font) -> None:
    """Draw the whole fight: the blobs, both health bars, and whatever prompt is showing."""
    surface.fill(TUNING.space_colour)

    pygame.draw.circle(surface, TUNING.boss_colour, TUNING.boss_centre, TUNING.boss_radius)
    pygame.draw.circle(surface, TUNING.pina_colour, TUNING.pina_centre, TUNING.pina_radius)

    draw_health_bar(
        surface,
        top=TUNING.boss_bar_top,
        health=fight.boss_health,
        maximum=TUNING.boss_max_health,
        colour=TUNING.boss_colour,
    )
    draw_health_bar(
        surface,
        top=TUNING.pina_bar_top,
        health=fight.pina_health,
        maximum=TUNING.pina_max_health,
        colour=TUNING.pina_colour,
    )

    if fight.state is FightState.WON:
        draw_centred_text(surface, "You saved the planet, Pina!", font=font, centre=TUNING.dodge_button_centre)
    elif fight.state is FightState.LOST:
        draw_centred_text(surface, "Ouch! Try again, Pina!", font=font, centre=TUNING.dodge_button_centre)
    elif fight.attack_incoming:
        pygame.draw.rect(surface, TUNING.dodge_colour, dodge_button_rect(), border_radius=16)
        draw_centred_text(surface, "DODGE!", font=font, centre=TUNING.dodge_button_centre)


def handle_click(fight: BossFight, position: Point) -> None:
    """Apply a mouse click to the fight, based on where on the screen it landed."""
    if fight.state is FightState.WON:
        fight.restart()
    elif fight.attack_incoming and dodge_button_rect().collidepoint(position):
        fight.dodge()
    elif is_inside_circle(position, centre=TUNING.boss_centre, radius=TUNING.boss_radius):
        fight.hit_boss()


async def run() -> None:
    """Open the game window and play until the player closes it."""
    pygame.init()
    screen = pygame.display.set_mode((TUNING.screen_width, TUNING.screen_height))
    pygame.display.set_caption("Planet Protectors")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 56)

    fight = BossFight()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_click(fight, event.pos)

        fight.tick(clock.get_time() / 1000)
        draw_fight(screen, fight, font=font)
        pygame.display.flip()

        clock.tick(TUNING.frames_per_second)
        await asyncio.sleep(0)

    pygame.quit()
