"""The game window: draws the fight and turns mouse clicks into actions.

The loop is `async` because the browser build (pygbag) requires it to yield once a frame.
This module owns everything visual; the rules it draws live in `bossfight`.
"""

import asyncio
import math
from collections.abc import Sequence

import pygame

from planet_protectors import art
from planet_protectors.bossfight import BossFight, FightState
from planet_protectors.tuning import TUNING, Colour, Point

BAR_BACKGROUND: Colour = (52, 44, 44)
MESSAGE_BORDER = 4
PAUSE_MESSAGE = ("Paused", "Press BACKSPACE to play on")


def is_inside_circle(point: Point, *, centre: Point, radius: int) -> bool:
    """Return whether a point falls within a circle."""
    return math.dist(point, centre) <= radius


def steering_direction(*, left_held: bool, right_held: bool) -> int:
    """Return the way the arrow keys are walking Pina, with both keys cancelling out."""
    return int(right_held) - int(left_held)


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


def draw_centred_text(
    surface: pygame.Surface,
    text: str,
    *,
    font: pygame.font.Font,
    centre: Point,
    colour: Colour = TUNING.text_colour,
) -> None:
    """Draw a line of text centred on a point."""
    rendered = font.render(text, True, colour)  # noqa: FBT003
    surface.blit(rendered, rendered.get_rect(center=centre))


def draw_message(surface: pygame.Surface, lines: Sequence[str], *, font: pygame.font.Font, centre: Point) -> None:
    """Draw lines of text on a card, so they can be read wherever on the planet they land."""
    rendered = [font.render(line, True, TUNING.text_colour) for line in lines]  # noqa: FBT003
    first_line_y = centre[1] - (len(rendered) - 1) * TUNING.message_line_spacing // 2
    rects = [
        image.get_rect(center=(centre[0], first_line_y + index * TUNING.message_line_spacing))
        for index, image in enumerate(rendered)
    ]

    card = rects[0].unionall(rects).inflate(48, 36)
    pygame.draw.rect(surface, TUNING.sky_colour, card, border_radius=18)
    pygame.draw.rect(surface, TUNING.ink_colour, card, MESSAGE_BORDER, border_radius=18)
    for image, rect in zip(rendered, rects, strict=True):
        surface.blit(image, rect)


def draw_fight(
    surface: pygame.Surface,
    fight: BossFight,
    *,
    font: pygame.font.Font,
    message_font: pygame.font.Font,
) -> None:
    """Draw the whole fight: the blobs, both health bars, and whatever prompt is showing."""
    art.draw_background(surface)
    art.draw_boss(surface, centre=fight.boss_centre)
    art.draw_pina(surface, centre=fight.pina_centre)

    draw_health_bar(
        surface,
        top=TUNING.boss_bar_top,
        health=fight.boss_health,
        maximum=TUNING.boss_max_health,
        colour=TUNING.boss_bar_colour,
    )
    draw_health_bar(
        surface,
        top=TUNING.pina_bar_top,
        health=fight.pina_health,
        maximum=TUNING.pina_max_health,
        colour=TUNING.pina_bar_colour,
    )

    if fight.paused:
        draw_message(surface, PAUSE_MESSAGE, font=message_font, centre=TUNING.message_centre)
    elif fight.state is FightState.WON:
        draw_message(surface, ["You saved the planet, Pina!"], font=message_font, centre=TUNING.message_centre)
    elif fight.state is FightState.LOST:
        draw_message(surface, ["Ouch! Try again, Pina!"], font=message_font, centre=TUNING.message_centre)
    elif fight.attack_incoming:
        pygame.draw.rect(surface, TUNING.dodge_colour, dodge_button_rect(), border_radius=16)
        draw_centred_text(
            surface,
            "DODGE!",
            font=font,
            centre=TUNING.dodge_button_centre,
            colour=TUNING.dodge_text_colour,
        )


def handle_key(fight: BossFight, key: int) -> None:
    """Apply a key press to the fight: `p` pauses it, backspace lets it carry on."""
    if key == pygame.K_p:
        fight.pause()
    elif key == pygame.K_BACKSPACE:
        fight.resume()


def handle_click(fight: BossFight, position: Point) -> None:
    """Apply a mouse click to the fight, based on where on the screen it landed."""
    if fight.paused:
        return
    if fight.state is FightState.WON:
        fight.restart()
    elif fight.attack_incoming and dodge_button_rect().collidepoint(position):
        fight.dodge()
    elif is_inside_circle(position, centre=fight.boss_centre, radius=TUNING.boss_radius):
        fight.hit_boss()


async def run() -> None:
    """Open the game window and play until the player closes it."""
    pygame.init()
    screen = pygame.display.set_mode((TUNING.screen_width, TUNING.screen_height))
    pygame.display.set_caption("Planet Protectors")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, TUNING.label_font_size)
    message_font = pygame.font.Font(None, TUNING.message_font_size)

    fight = BossFight()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_click(fight, event.pos)
            elif event.type == pygame.KEYDOWN:
                handle_key(fight, event.key)

        keys = pygame.key.get_pressed()
        fight.steer_pina(steering_direction(left_held=keys[pygame.K_LEFT], right_held=keys[pygame.K_RIGHT]))

        fight.tick(clock.get_time() / 1000)
        draw_fight(screen, fight, font=font, message_font=message_font)
        pygame.display.flip()

        clock.tick(TUNING.frames_per_second)
        await asyncio.sleep(0)

    pygame.quit()
