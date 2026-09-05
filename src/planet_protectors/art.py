"""Draws the red planet, Pina, and the raccoon boss.

Every shape is built from pygame primitives around a centre point, so a character can be
moved by moving its centre. Nothing here reads the fight; it only paints.
"""

import math

import pygame

from planet_protectors.tuning import TUNING, Colour, Point

MARKER_WIDTH = 5
STREAK_WIDTH = 2
LOOP_HEIGHT = 20
LOOP_SPACING = 9
HIGHLIGHT_COLOUR: Colour = (232, 118, 96)


def _offset(centre: Point, step: Point) -> Point:
    """Return the point `step` away from `centre`."""
    return (centre[0] + step[0], centre[1] + step[1])


def _polygon(centre: Point, shape: tuple[Point, ...]) -> list[Point]:
    """Return a shape given in offsets from `centre` as absolute points."""
    return [_offset(centre, step) for step in shape]


def _ellipse(centre: Point, size: Point) -> pygame.Rect:
    """Return the rect an ellipse of `size` centred on `centre` fills."""
    rect = pygame.Rect((0, 0), size)
    rect.center = centre
    return rect


def _scribble(surface: pygame.Surface, *, centre: Point, radius: int, colour: Colour, spacing: int) -> None:
    """Rule vertical lines inside a circle, for the look of a shape filled in with a marker."""
    for x in range(centre[0] - radius + spacing, centre[0] + radius, spacing):
        half_height = round(math.sqrt(radius**2 - (x - centre[0]) ** 2)) - 5
        if half_height > 0:
            pygame.draw.line(surface, colour, (x, centre[1] - half_height), (x, centre[1] + half_height), STREAK_WIDTH)


def draw_background(surface: pygame.Surface) -> None:
    """Fill the screen with the red planet: pale sky, a tree, a hedge, and red ground."""
    surface.fill(TUNING.sky_colour)
    _draw_hedge(surface)
    _draw_ground(surface)
    _draw_tree(surface)


def _draw_ground(surface: pygame.Surface) -> None:
    ground = pygame.Rect(0, TUNING.ground_top, TUNING.screen_width, TUNING.screen_height - TUNING.ground_top)
    pygame.draw.rect(surface, TUNING.ground_colour, ground)
    for x in range(0, TUNING.screen_width + 40, 40):
        pygame.draw.circle(surface, TUNING.ground_colour, (x, ground.top), 5 + (x // 40) % 3 * 3)
    for row, y in enumerate(range(ground.top + 14, ground.bottom, 17)):
        for x in range(-60 + (row % 3) * 50, ground.right, 160):
            pygame.draw.line(surface, HIGHLIGHT_COLOUR, (x, y), (x + 118, y), STREAK_WIDTH)


def _draw_hedge(surface: pygame.Surface) -> None:
    for index, x in enumerate(range(560, TUNING.screen_width + 60, 44)):
        bush = (x, TUNING.ground_top + 10)
        radius = 44 + (index % 3) * 20
        pygame.draw.circle(surface, TUNING.bush_colour, bush, radius)
        _scribble(surface, centre=bush, radius=radius, colour=TUNING.ground_colour, spacing=12)


def _draw_tree(surface: pygame.Surface) -> None:
    trunk = pygame.Rect(0, 0, 16, TUNING.ground_top - 200)
    trunk.midtop = (86, 200)
    pygame.draw.rect(surface, TUNING.trunk_colour, trunk)

    canopy = ((0, 0, 84), (-46, 20, 58), (48, 16, 60), (6, -40, 56))
    for offset_x, offset_y, radius in canopy:
        pygame.draw.circle(surface, TUNING.tree_colour, (86 + offset_x, 214 + offset_y), radius)
    for offset_x, offset_y, radius in canopy:
        _scribble(
            surface,
            centre=(86 + offset_x, 214 + offset_y),
            radius=radius,
            colour=HIGHLIGHT_COLOUR,
            spacing=13,
        )


def draw_pina(surface: pygame.Surface, *, centre: Point) -> None:
    """Draw Pina: a red blob with teal hair, teal hands, and a wide smile."""
    _draw_pina_limbs(surface, centre=centre)
    pygame.draw.circle(surface, TUNING.pina_colour, centre, TUNING.pina_radius)
    _draw_pina_face(surface, centre=centre)
    _draw_hair(surface, centre=centre)


def _draw_pina_limbs(surface: pygame.Surface, *, centre: Point) -> None:
    for shoulder, hand, hand_size in (((-40, -5), (-85, 15), (26, 32)), ((38, -18), (80, -40), (30, 26))):
        pygame.draw.line(surface, TUNING.ink_colour, _offset(centre, shoulder), _offset(centre, hand), MARKER_WIDTH)
        pygame.draw.ellipse(surface, TUNING.teal_colour, _ellipse(_offset(centre, hand), hand_size))

    for hip, foot in (((-16, 46), (-22, 88)), ((14, 46), (20, 88))):
        pygame.draw.line(surface, TUNING.ink_colour, _offset(centre, hip), _offset(centre, foot), MARKER_WIDTH)
        for toe in (-14, 0, 14):
            pygame.draw.line(
                surface,
                TUNING.ink_colour,
                _offset(centre, foot),
                _offset(centre, (foot[0] + toe, foot[1] + 12)),
                STREAK_WIDTH + 1,
            )


def _draw_pina_face(surface: pygame.Surface, *, centre: Point) -> None:
    for x, y in ((-18, -14), (16, -16)):
        pygame.draw.circle(surface, TUNING.ink_colour, _offset(centre, (x, y)), 8)
    smile = _ellipse(_offset(centre, (0, 4)), (62, 44))
    pygame.draw.arc(surface, TUNING.ink_colour, smile, math.pi, math.tau, MARKER_WIDTH)


def _draw_hair(surface: pygame.Surface, *, centre: Point) -> None:
    for strand in HAIR_STRANDS:
        pygame.draw.lines(
            surface,
            TUNING.teal_colour,
            False,  # noqa: FBT003
            [_offset(centre, step) for step in strand],
            MARKER_WIDTH,
        )


# Three strands from one tuft on top of Pina's head, each arcing right to a hooked tip.
HAIR_STRANDS: tuple[tuple[Point, ...], ...] = (
    ((-14, -44), (-12, -68), (-2, -86), (16, -95), (34, -94), (45, -85), (48, -76), (54, -80)),
    ((-12, -44), (-4, -64), (8, -76), (24, -79), (37, -72), (41, -64), (48, -68)),
    ((-9, -44), (2, -56), (16, -62), (30, -59), (38, -50), (44, -54)),
)

HEAD_SHAPE: tuple[Point, ...] = (
    (-92, -62),
    (-72, -88),
    (-30, -96),
    (30, -96),
    (72, -88),
    (92, -62),
    (74, 6),
    (40, 52),
    (0, 92),
    (-40, 52),
    (-74, 6),
)
EAR_SHAPE: tuple[Point, ...] = ((-64, -84), (-46, -114), (-26, -90))


def draw_boss(
    surface: pygame.Surface,
    *,
    centre: Point,
    colour: Colour = TUNING.boss_colour,
    shade_colour: Colour = TUNING.boss_shade_colour,
    opacity: float = 1.0,
) -> None:
    """Draw the boss: a raccoon's face on two small legs, in the colours and solidity given."""
    if opacity >= 1:
        _paint_boss(surface, centre=centre, colour=colour, shade_colour=shade_colour)
        return

    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    _paint_boss(layer, centre=centre, colour=colour, shade_colour=shade_colour)
    layer.set_alpha(round(255 * opacity))
    surface.blit(layer, (0, 0))


def _paint_boss(surface: pygame.Surface, *, centre: Point, colour: Colour, shade_colour: Colour) -> None:
    _draw_boss_legs(surface, centre=centre)
    for ear in (EAR_SHAPE, tuple((-dx, dy) for dx, dy in EAR_SHAPE)):
        pygame.draw.polygon(surface, TUNING.ink_colour, _polygon(centre, ear))

    pygame.draw.polygon(surface, colour, _polygon(centre, HEAD_SHAPE))
    for top_x, bottom_x in ((-78, -34), (-58, -22), (58, 22), (78, 34)):
        pygame.draw.line(
            surface,
            shade_colour,
            _offset(centre, (top_x, -72)),
            _offset(centre, (bottom_x, 40)),
            STREAK_WIDTH,
        )
    pygame.draw.polygon(surface, shade_colour, _polygon(centre, HEAD_SHAPE), MARKER_WIDTH)
    _draw_boss_face(surface, centre=centre, shade_colour=shade_colour)


def _draw_boss_face(surface: pygame.Surface, *, centre: Point, shade_colour: Colour) -> None:
    for x in (-42, 42):
        pygame.draw.ellipse(surface, TUNING.ink_colour, _ellipse(_offset(centre, (x, -25)), (46, 70)))
    for brow, tip in (((-30, -66), (-14, -48)), ((30, -66), (14, -48))):
        pygame.draw.line(surface, TUNING.ink_colour, _offset(centre, brow), _offset(centre, tip), MARKER_WIDTH)

    pygame.draw.ellipse(surface, TUNING.ink_colour, _ellipse(_offset(centre, (0, 46)), (26, 20)))
    pygame.draw.line(surface, shade_colour, _offset(centre, (0, 56)), _offset(centre, (0, 84)), STREAK_WIDTH)


def _draw_boss_legs(surface: pygame.Surface, *, centre: Point) -> None:
    for hip, knee, foot in (((-26, 60), (-36, 92), (-30, 116)), ((26, 60), (36, 92), (30, 116))):
        pygame.draw.lines(
            surface,
            TUNING.ink_colour,
            False,  # noqa: FBT003
            [_offset(centre, hip), _offset(centre, knee), _offset(centre, foot)],
            MARKER_WIDTH,
        )
        pygame.draw.circle(surface, TUNING.ink_colour, _offset(centre, foot), 9)


def draw_tornado(surface: pygame.Surface, *, tip: Point, radius: int) -> None:
    """Draw a tornado: scribbled loops stacked widest at the top, tapering down to `tip`."""
    height = round(TUNING.tornado_height * radius / TUNING.tornado_full_radius)
    colours = TUNING.tornado_colours
    for index, y in enumerate(range(tip[1] - LOOP_HEIGHT // 2, tip[1] - height + LOOP_HEIGHT // 2, -LOOP_SPACING)):
        up_the_funnel = (tip[1] - y) / height
        half_width = round(radius * up_the_funnel) - (index % 3) * 3
        if half_width < STREAK_WIDTH:
            continue
        loop = _ellipse((tip[0], y), (2 * half_width, LOOP_HEIGHT))
        pygame.draw.ellipse(surface, colours[index % len(colours)], loop)
        pygame.draw.ellipse(surface, colours[(index + 1) % len(colours)], loop, STREAK_WIDTH)


def draw_tornado_warning(surface: pygame.Surface, *, tip: Point) -> None:
    """Mark the ground a tornado is about to land on, so there is time to walk away."""
    pygame.draw.circle(surface, TUNING.tornado_warning_colour, tip, TUNING.tornado_warning_radius)
