import pygame
import pytest

from planet_protectors.app import draw_centred_text, draw_fight, draw_message, handle_click
from planet_protectors.bossfight import BossFight, FightState
from planet_protectors.tuning import TUNING, Colour
from tests.pixels import colour_at

EMPTY_SPACE = (40, 250)

# A colour that appears nowhere in the game, so "still this colour" means "never painted".
UNPAINTED: Colour = (255, 0, 255)

# How far apart two colours must be, summed across red, green, and blue, to be told apart
# on a screen in a bright room. Pale grey on white scores about 25; black on white, 700.
LEGIBLE_CONTRAST = 200


def contrast(first: Colour, second: Colour) -> int:
    """Return how far apart two colours are, summed across the three channels."""
    return sum(abs(one - other) for one, other in zip(first, second, strict=True))


class TestHandleClick:
    @staticmethod
    def test_clicking_the_boss_damages_it() -> None:
        fight = BossFight()

        handle_click(fight, TUNING.boss_centre)

        assert fight.boss_health == TUNING.boss_max_health - TUNING.hit_damage

    @staticmethod
    def test_clicking_empty_space_does_nothing() -> None:
        fight = BossFight()

        handle_click(fight, EMPTY_SPACE)

        assert fight.boss_health == TUNING.boss_max_health

    @staticmethod
    def test_clicking_the_dodge_button_dodges_an_incoming_attack() -> None:
        fight = BossFight(dodge_window_left=TUNING.dodge_window_seconds)

        handle_click(fight, TUNING.dodge_button_centre)

        assert not fight.attack_incoming

    @staticmethod
    def test_clicking_the_dodge_button_with_no_attack_incoming_does_nothing() -> None:
        fight = BossFight()

        handle_click(fight, TUNING.dodge_button_centre)

        assert fight.boss_health == TUNING.boss_max_health
        assert fight.pina_health == TUNING.pina_max_health

    @staticmethod
    def test_the_boss_can_still_be_hit_while_an_attack_is_incoming() -> None:
        fight = BossFight(dodge_window_left=TUNING.dodge_window_seconds)

        handle_click(fight, TUNING.boss_centre)

        assert fight.boss_health == TUNING.boss_max_health - TUNING.hit_damage
        assert fight.attack_incoming

    @staticmethod
    def test_clicking_after_winning_starts_the_fight_again() -> None:
        fight = BossFight(boss_health=0, state=FightState.WON)

        handle_click(fight, EMPTY_SPACE)

        assert fight.state is FightState.FIGHTING
        assert fight.boss_health == TUNING.boss_max_health


class TestDrawCentredText:
    @staticmethod
    def test_the_messages_are_legible_against_the_sky() -> None:
        """The messages are written straight onto the planet's sky, not onto a panel.

        A pale colour on a pale sky leaves the win and lose messages all but invisible, and
        nothing else in the game would fail if that happened - so this test is the only
        thing standing between Pina and an unreadable "You saved the planet!".
        """
        pygame.font.init()
        surface = pygame.Surface((400, 100))
        surface.fill(TUNING.sky_colour)

        draw_centred_text(surface, "You saved the planet, Pina!", font=pygame.font.Font(None, 56), centre=(200, 50))

        painted = [colour_at(surface, (x, y)) for x in range(400) for y in range(100)]
        assert max(contrast(colour, TUNING.sky_colour) for colour in painted) >= LEGIBLE_CONTRAST


class TestDrawMessage:
    @staticmethod
    def test_the_message_sits_on_a_card_that_hides_the_art_behind_it() -> None:
        """The win and lose messages are wide enough to land on Pina, the boss, or a tree.

        Rather than pick a gap in the art and hope it stays a gap, the message brings its
        own background with it, so it can be read whatever it happens to be sitting on.
        """
        pygame.font.init()
        surface = pygame.Surface((600, 200))
        surface.fill(TUNING.pina_colour)

        draw_message(surface, "Ouch! Try again, Pina!", font=pygame.font.Font(None, 56), centre=(300, 100))

        just_inside_the_card = [(300, 78), (300, 122), (170, 100), (430, 100)]
        assert [colour_at(surface, point) for point in just_inside_the_card] == [TUNING.sky_colour] * 4


class TestDrawFight:
    @staticmethod
    @pytest.mark.parametrize("state", list(FightState))
    def test_the_frame_is_painted_from_edge_to_edge(state: FightState) -> None:
        """A frame with a gap in it means the planet was drawn too small for the screen.

        Nothing else notices: the game keeps running and the browser build keeps loading,
        it just has a bar of nothing down one side.
        """
        pygame.font.init()
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))
        surface.fill(UNPAINTED)
        font = pygame.font.Font(None, TUNING.label_font_size)

        draw_fight(surface, BossFight(state=state), font=font, message_font=font)

        swept = [
            colour_at(surface, (x, y))
            for x in range(0, TUNING.screen_width, 4)
            for y in range(0, TUNING.screen_height, 4)
        ]
        assert UNPAINTED not in swept
