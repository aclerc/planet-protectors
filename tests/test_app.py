import pygame
import pytest

from planet_protectors.app import draw_centred_text, draw_fight, draw_message, handle_click, steering_direction
from planet_protectors.bossfight import BossFight, FightState
from planet_protectors.tuning import TUNING, Colour
from tests.pixels import colour_at

EMPTY_SPACE = (40, 250)

# Somewhere the boss can drift to, far enough from where it starts that a click on one is
# nowhere near the other.
DRIFTED_TO = (300, 300)

# Somewhere along the ground Pina can walk to, well away from where he starts.
WALKED_TO = 620

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
    def test_clicking_the_boss_where_it_has_drifted_to_damages_it() -> None:
        fight = BossFight(boss_x=DRIFTED_TO[0], boss_y=DRIFTED_TO[1])

        handle_click(fight, DRIFTED_TO)

        assert fight.boss_health == TUNING.boss_max_health - TUNING.hit_damage

    @staticmethod
    def test_clicking_where_the_boss_began_misses_once_it_has_drifted_away() -> None:
        fight = BossFight(boss_x=DRIFTED_TO[0], boss_y=DRIFTED_TO[1])

        handle_click(fight, TUNING.boss_centre)

        assert fight.boss_health == TUNING.boss_max_health

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

    @staticmethod
    def test_the_boss_is_drawn_where_it_has_drifted_to() -> None:
        """The frame has to follow the boss's live position, not the tuning constant.

        Drawing it at the constant leaves a boss painted where it no longer is: the
        clicking still works, it just lands on empty planet.
        """
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        frames = []
        for fight in (BossFight(boss_x=DRIFTED_TO[0], boss_y=DRIFTED_TO[1]), BossFight()):
            surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))
            draw_fight(surface, fight, font=font, message_font=font)
            frames.append(pygame.image.tobytes(surface, "RGB"))

        assert frames[0] != frames[1]

    @staticmethod
    def test_pina_is_drawn_where_he_has_walked_to() -> None:
        """The same trap as the boss: drawing Pina at the tuning constant leaves him behind."""
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        frames = []
        for fight in (BossFight(pina_x=WALKED_TO), BossFight()):
            surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))
            draw_fight(surface, fight, font=font, message_font=font)
            frames.append(pygame.image.tobytes(surface, "RGB"))

        assert frames[0] != frames[1]


class TestSteeringDirection:
    @staticmethod
    def test_holding_right_steers_right() -> None:
        assert steering_direction(left_held=False, right_held=True) == 1

    @staticmethod
    def test_holding_left_steers_left() -> None:
        assert steering_direction(left_held=True, right_held=False) == -1

    @staticmethod
    def test_holding_neither_key_stands_still() -> None:
        assert steering_direction(left_held=False, right_held=False) == 0

    @staticmethod
    def test_holding_both_keys_stands_still() -> None:
        """Both arrows at once is a game of its own once you are five."""
        assert steering_direction(left_held=True, right_held=True) == 0
