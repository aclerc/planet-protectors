"""Pins down where each piece of art lands on the screen.

The drawing functions return nothing, so these tests look at the game the way a player
does: at the pixels. Each one paints a surface a colour that appears nowhere in the game,
draws a single thing, and then asks which pixels changed.

That is enough to catch the mistakes that actually happen with drawing code and that no
type checker will find - art drawn off the edge of the screen, a boss whose head does not
cover the circle the player has to click on, or a limb that sprawls halfway across the
planet because a coordinate was added instead of subtracted.
"""

import pygame

from planet_protectors import art
from planet_protectors.tuning import TUNING, Colour, Point
from tests.pixels import colour_at

# A colour that appears nowhere in the game, so "still this colour" means "never painted".
SENTINEL: Colour = (255, 0, 255)

# How far from their centres Pina and the boss are allowed to reach, limbs included.
PINA_REACH: Point = (110, 120)
BOSS_REACH: Point = (110, 140)

# Pixels are sampled on a grid rather than one by one; a stride this size cannot step over
# any part of the art, and keeps a whole-screen sweep quick.
SWEEP_STRIDE = 4


def blank_surface() -> pygame.Surface:
    """Return a screen-sized surface painted the sentinel colour."""
    surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))
    surface.fill(SENTINEL)
    return surface


def painted_outside(surface: pygame.Surface, *, box: pygame.Rect) -> list[Point]:
    """Return the sampled points that were painted on despite falling outside `box`."""
    return [
        (x, y)
        for x in range(0, surface.get_width(), SWEEP_STRIDE)
        for y in range(0, surface.get_height(), SWEEP_STRIDE)
        if not box.collidepoint(x, y) and colour_at(surface, (x, y)) != SENTINEL
    ]


def reach_box(centre: Point, reach: Point) -> pygame.Rect:
    """Return the box a character drawn at `centre` is expected to stay inside."""
    box = pygame.Rect((0, 0), (2 * reach[0], 2 * reach[1]))
    box.center = centre
    return box


class TestDrawBackground:
    @staticmethod
    def test_the_sky_fills_the_top_of_the_screen() -> None:
        surface = blank_surface()

        art.draw_background(surface)

        assert colour_at(surface, (TUNING.screen_width // 2, 10)) == TUNING.sky_colour

    @staticmethod
    def test_red_ground_fills_the_bottom_of_the_screen() -> None:
        surface = blank_surface()

        art.draw_background(surface)

        assert colour_at(surface, (TUNING.screen_width // 2, TUNING.screen_height - 10)) == TUNING.ground_colour

    @staticmethod
    def test_the_tree_stands_on_the_left_above_the_ground() -> None:
        surface = blank_surface()

        art.draw_background(surface)

        canopy = [colour_at(surface, (x, TUNING.ground_top // 2)) for x in range(20, 140, 10)]
        assert TUNING.tree_colour in canopy

    @staticmethod
    def test_bushes_stand_on_the_ground_over_on_the_right() -> None:
        surface = blank_surface()

        art.draw_background(surface)

        just_above_the_ground = [colour_at(surface, (x, TUNING.ground_top - 20)) for x in range(600, 940, 10)]
        assert TUNING.bush_colour in just_above_the_ground

    @staticmethod
    def test_no_corner_of_the_screen_is_left_unpainted() -> None:
        surface = blank_surface()

        art.draw_background(surface)

        swept = [
            colour_at(surface, (x, y))
            for x in range(0, TUNING.screen_width, SWEEP_STRIDE)
            for y in range(0, TUNING.screen_height, SWEEP_STRIDE)
        ]
        assert SENTINEL not in swept


class TestDrawPina:
    @staticmethod
    def test_her_body_is_red_at_her_centre() -> None:
        surface = blank_surface()

        art.draw_pina(surface, centre=TUNING.pina_centre)

        assert colour_at(surface, TUNING.pina_centre) == TUNING.pina_colour

    @staticmethod
    def test_her_hair_stands_up_above_her_head() -> None:
        surface = blank_surface()

        art.draw_pina(surface, centre=TUNING.pina_centre)

        above_her_head = TUNING.pina_centre[1] - TUNING.pina_radius
        strip = [
            colour_at(surface, (x, y))
            for x in range(TUNING.pina_centre[0] - 40, TUNING.pina_centre[0] + 40)
            for y in range(above_her_head - 45, above_her_head)
        ]
        assert TUNING.teal_colour in strip

    @staticmethod
    def test_her_hair_sweeps_over_to_the_right() -> None:
        """In the drawing every strand sprouts from one tuft and arcs away to the right.

        Three strands standing straight up on top of her head is a different character, so
        this pins down the sweep: teal well out to her right, and none of it out to her left.
        """
        surface = blank_surface()
        centre_x, top = TUNING.pina_centre[0], TUNING.pina_centre[1] - TUNING.pina_radius

        art.draw_pina(surface, centre=TUNING.pina_centre)

        swept_right = [
            colour_at(surface, (x, y)) for x in range(centre_x + 34, centre_x + 60) for y in range(top - 50, top)
        ]
        out_to_the_left = [
            colour_at(surface, (x, y)) for x in range(centre_x - 60, centre_x - 24) for y in range(top - 50, top)
        ]
        assert TUNING.teal_colour in swept_right
        assert TUNING.teal_colour not in out_to_the_left

    @staticmethod
    def test_her_hands_are_teal_and_out_to_her_sides() -> None:
        surface = blank_surface()

        art.draw_pina(surface, centre=TUNING.pina_centre)

        beyond_her_body = TUNING.pina_centre[0] + TUNING.pina_radius + 10
        strip = [
            colour_at(surface, (x, y))
            for x in range(beyond_her_body, beyond_her_body + 50)
            for y in range(TUNING.pina_centre[1] - 60, TUNING.pina_centre[1] + 10)
        ]
        assert TUNING.teal_colour in strip

    @staticmethod
    def test_she_stays_within_arms_and_legs_reach_of_her_centre() -> None:
        surface = blank_surface()

        art.draw_pina(surface, centre=TUNING.pina_centre)

        assert painted_outside(surface, box=reach_box(TUNING.pina_centre, PINA_REACH)) == []


class TestDrawBoss:
    @staticmethod
    def test_the_head_covers_the_circle_the_player_clicks_on() -> None:
        surface = blank_surface()
        centre_x, centre_y = TUNING.boss_centre
        half = TUNING.boss_radius // 2

        art.draw_boss(surface, centre=TUNING.boss_centre)

        clickable = [
            TUNING.boss_centre,
            (centre_x - half, centre_y),
            (centre_x + half, centre_y),
            (centre_x, centre_y - half),
            (centre_x, centre_y + half),
        ]
        assert [point for point in clickable if colour_at(surface, point) == SENTINEL] == []

    @staticmethod
    def test_it_has_two_dark_eye_patches_side_by_side() -> None:
        surface = blank_surface()
        centre_x, centre_y = TUNING.boss_centre

        art.draw_boss(surface, centre=TUNING.boss_centre)

        eye_line = [
            colour_at(surface, (x, centre_y - 20)) == TUNING.ink_colour for x in range(centre_x - 80, centre_x + 80)
        ]
        patches = sum(1 for before, now in zip([False, *eye_line], eye_line, strict=False) if now and not before)
        assert patches == 2

    @staticmethod
    def test_it_has_two_small_feet_below_its_head() -> None:
        surface = blank_surface()
        centre_x, centre_y = TUNING.boss_centre

        art.draw_boss(surface, centre=TUNING.boss_centre)

        below_the_head = [
            colour_at(surface, (x, centre_y + TUNING.boss_radius + 25)) for x in range(centre_x - 60, centre_x + 60)
        ]
        assert TUNING.ink_colour in below_the_head

    @staticmethod
    def test_it_stays_within_reach_of_its_centre() -> None:
        surface = blank_surface()

        art.draw_boss(surface, centre=TUNING.boss_centre)

        assert painted_outside(surface, box=reach_box(TUNING.boss_centre, BOSS_REACH)) == []
