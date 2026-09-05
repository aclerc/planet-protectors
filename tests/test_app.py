import pygame
import pytest

from planet_protectors.app import (
    BOSS_NAME,
    INSTRUCTIONS,
    PINA_NAME,
    WIN_MESSAGE,
    dodge_button_rect,
    draw_centred_text,
    draw_fight,
    draw_instructions,
    draw_message,
    handle_click,
    handle_key,
    steering_direction,
)
from planet_protectors.bossfight import BossFight, FightState, Tornado
from planet_protectors.tuning import TUNING, Colour, Point
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

# Pixels are sampled on a grid rather than one by one; a stride this size cannot step over
# any part of the art, and keeps a whole-screen sweep quick.
SWEEP_STRIDE = 4


# The band across the middle of the screen the message cards are written in. The names on
# the health bars are the only other white in the game, and both bars sit outside it.
MESSAGE_BAND = pygame.Rect(0, 300, TUNING.screen_width, 120)

# The box the boss and its legs stay inside, wherever it has drifted to.
BOSS_BOX = pygame.Rect(0, 0, 220, 280)


def contrast(first: Colour, second: Colour) -> int:
    """Return how far apart two colours are, summed across the three channels."""
    return sum(abs(one - other) for one, other in zip(first, second, strict=True))


def message_is_showing(surface: pygame.Surface) -> bool:
    """Return whether a message card has been written across the middle of a frame."""
    return any(
        colour_at(surface, (x, y)) == TUNING.text_colour
        for x in range(MESSAGE_BAND.left, MESSAGE_BAND.right, 2)
        for y in range(MESSAGE_BAND.top, MESSAGE_BAND.bottom, 2)
    )


def boss_box_at(centre: Point) -> pygame.Rect:
    """Return the box the boss fills when it is drawn at `centre`."""
    box = BOSS_BOX.copy()
    box.center = centre
    return box


def frame_of(fight: BossFight) -> pygame.Surface:
    """Draw one frame of a fight, the way the game draws it every tick."""
    pygame.font.init()
    font = pygame.font.Font(None, TUNING.label_font_size)
    surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))
    draw_fight(surface, fight, font=font, message_font=font, bar_font=font)
    return surface


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
    def test_clicking_after_winning_does_not_start_the_fight_again() -> None:
        """A win is worth looking at; a stray click should not wipe it off the screen."""
        fight = BossFight(boss_health=0, state=FightState.WON)

        handle_click(fight, EMPTY_SPACE)

        assert fight.state is FightState.WON


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

        draw_message(surface, ["Ouch! Try again, Pina!"], font=pygame.font.Font(None, 56), centre=(300, 100))

        just_inside_the_card = [(300, 78), (300, 122), (170, 100), (430, 100)]
        assert [colour_at(surface, point) for point in just_inside_the_card] == [TUNING.sky_colour] * 4

    @staticmethod
    def test_a_second_line_is_written_below_the_first() -> None:
        """The pause screen needs two lines: what has happened, and how to undo it.

        Drawing only the first would leave a player looking at "Paused" with no way of
        knowing which key brings the fight back, and nothing else would complain.
        """
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.message_font_size)
        surface = pygame.Surface((600, 300))
        surface.fill(TUNING.pina_colour)

        draw_message(surface, ["Paused", "Press BACKSPACE to play on"], font=font, centre=(300, 150))

        # The middle of the second line, which is further down than one centred line reaches.
        second_line = 150 + TUNING.message_line_spacing // 2
        across_the_card = [colour_at(surface, (x, second_line)) for x in range(200, 400)]
        assert TUNING.text_colour in across_the_card


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

        draw_fight(surface, BossFight(state=state), font=font, message_font=font, bar_font=font)

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
            draw_fight(surface, fight, font=font, message_font=font, bar_font=font)
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
            draw_fight(surface, fight, font=font, message_font=font, bar_font=font)
            frames.append(pygame.image.tobytes(surface, "RGB"))

        assert frames[0] != frames[1]


class TestNamingTheHealthBars:
    """Two bars with nothing written on them leave a player guessing which one is theirs."""

    @staticmethod
    @pytest.mark.parametrize("top", [TUNING.boss_bar_top, TUNING.pina_bar_top])
    def test_a_name_is_written_on_the_bar(top: int) -> None:
        """White appears nowhere else along a bar, so white on one is the name and nothing else."""
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))

        draw_fight(
            surface,
            BossFight(),
            font=font,
            message_font=font,
            bar_font=pygame.font.Font(None, TUNING.bar_font_size),
        )

        along_the_bar = [
            colour_at(surface, (x, y))
            for x in range(TUNING.bar_margin, TUNING.screen_width - TUNING.bar_margin)
            for y in range(top, top + TUNING.bar_height)
        ]
        assert TUNING.text_colour in along_the_bar

    @staticmethod
    @pytest.mark.parametrize("name", [BOSS_NAME, PINA_NAME])
    def test_a_name_fits_inside_its_bar(name: str) -> None:
        """A name taller than the bar spills over the sky above it and the planet below it."""
        pygame.font.init()
        bar_font = pygame.font.Font(None, TUNING.bar_font_size)

        width, height = bar_font.size(name)

        assert height <= TUNING.bar_height
        assert width < TUNING.screen_width - 2 * TUNING.bar_margin


class TestDrawTheDodgeButton:
    @staticmethod
    def test_the_dodge_label_is_dark_against_its_yellow_button() -> None:
        """The messages are white for the dark sky behind them; the button is pale yellow.

        White on that yellow is faint enough to lose in a bright room, so the button keeps
        its own dark label rather than sharing the colour the messages use.
        """
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))

        draw_fight(
            surface,
            BossFight(dodge_window_left=TUNING.dodge_window_seconds),
            font=font,
            message_font=font,
            bar_font=font,
        )

        button = dodge_button_rect()
        across_the_label = [colour_at(surface, (x, button.centery)) for x in range(button.left, button.right)]
        assert TUNING.dodge_text_colour in across_the_label
        assert contrast(TUNING.dodge_text_colour, TUNING.dodge_colour) >= LEGIBLE_CONTRAST


class TestWinningTheFight:
    """What the frame shows once the boss is beaten: it turns red, fades, then the card."""

    @staticmethod
    def test_it_says_which_key_plays_again() -> None:
        """Nothing else on the win screen says how to play on; a click no longer does it."""
        assert "R" in " ".join(WIN_MESSAGE).upper()

    @staticmethod
    def test_the_beaten_boss_is_drawn_red() -> None:
        """Turning red is how a five-year-old sees the fight has been won."""
        surface = frame_of(BossFight(boss_health=0, state=FightState.WON))

        assert colour_at(surface, TUNING.boss_centre) == TUNING.boss_defeated_colour

    @staticmethod
    def test_the_beaten_boss_is_gone_once_it_has_faded() -> None:
        surface = frame_of(BossFight(boss_health=0, state=FightState.WON, seconds_to_vanish=0.0))

        assert colour_at(surface, TUNING.boss_centre) == TUNING.sky_colour

    @staticmethod
    def test_the_win_message_waits_until_the_beaten_boss_has_faded_away() -> None:
        """The card sits where the boss is fading; showing it early hides the reward."""
        surface = frame_of(BossFight(boss_health=0, state=FightState.WON))

        assert not message_is_showing(surface)

    @staticmethod
    def test_the_win_message_is_shown_once_the_boss_has_gone() -> None:
        surface = frame_of(BossFight(boss_health=0, state=FightState.WON, seconds_to_vanish=0.0))

        assert message_is_showing(surface)

    @staticmethod
    def test_a_won_fight_shows_no_dodge_button() -> None:
        """An attack can still be in the air when the winning hit lands."""
        won = BossFight(boss_health=0, state=FightState.WON, dodge_window_left=TUNING.dodge_window_seconds)

        surface = frame_of(won)

        assert colour_at(surface, TUNING.dodge_button_centre) != TUNING.dodge_colour


class TestDrawInstructions:
    """The screen the game opens on, which is the only place the controls are written down."""

    @staticmethod
    def test_it_says_how_to_do_every_thing_the_player_can_do() -> None:
        """A control missing from here is a control nobody will find; the game teaches nothing else."""
        written = " ".join(INSTRUCTIONS).upper()

        assert "ARROW" in written
        assert "CLICK" in written
        assert "DODGE" in written
        assert "TORNADO" in written
        assert "P" in written
        assert "BACKSPACE" in written

    @staticmethod
    def test_it_is_drawn_on_a_card_over_the_planet() -> None:
        pygame.font.init()
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))
        surface.fill(UNPAINTED)

        draw_instructions(surface, font=pygame.font.Font(None, TUNING.message_font_size))

        swept = [
            colour_at(surface, (x, y))
            for x in range(0, TUNING.screen_width, SWEEP_STRIDE)
            for y in range(0, TUNING.screen_height, SWEEP_STRIDE)
        ]
        assert UNPAINTED not in swept
        assert TUNING.text_colour in swept

    @staticmethod
    def test_every_line_of_it_fits_on_the_screen() -> None:
        """Six lines of text at message size is close enough to the screen edges to be worth pinning."""
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.message_font_size)

        widest = max(font.size(line)[0] for line in INSTRUCTIONS)
        tall = len(INSTRUCTIONS) * TUNING.message_line_spacing

        assert widest < TUNING.screen_width
        assert tall < TUNING.screen_height


class TestDrawingTornadoes:
    @staticmethod
    def test_the_warning_circle_is_drawn_where_a_tornado_will_land() -> None:
        """The circle is the only warning there is, so a frame without it is a frame that lies."""
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))

        draw_fight(surface, BossFight(tornado=Tornado(x=700)), font=font, message_font=font, bar_font=font)

        assert colour_at(surface, (700, TUNING.ground_top)) == TUNING.tornado_warning_colour

    @staticmethod
    def test_the_funnel_is_drawn_once_the_tornado_has_landed() -> None:
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))

        draw_fight(
            surface,
            BossFight(tornado=Tornado(x=700, seconds_to_land=0.0)),
            font=font,
            message_font=font,
            bar_font=font,
        )

        above_the_ground = {
            colour_at(surface, (x, y))
            for x in range(660, 740, 2)
            for y in range(TUNING.ground_top - 60, TUNING.ground_top, 2)
        }
        assert above_the_ground & set(TUNING.tornado_colours)

    @staticmethod
    def test_the_warning_circle_goes_once_the_tornado_has_landed() -> None:
        """Leaving it behind would mark ground that is no longer the ground to avoid."""
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))

        draw_fight(
            surface,
            BossFight(tornado=Tornado(x=700, seconds_to_land=0.0)),
            font=font,
            message_font=font,
            bar_font=font,
        )

        swept = [
            colour_at(surface, (x, y))
            for x in range(600, 800, 4)
            for y in range(TUNING.ground_top - 40, TUNING.ground_top + 40, 4)
        ]
        assert TUNING.tornado_warning_colour not in swept

    @staticmethod
    def test_a_frame_without_a_tornado_has_no_funnel_on_it() -> None:
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))

        draw_fight(surface, BossFight(), font=font, message_font=font, bar_font=font)

        swept = {
            colour_at(surface, (x, y))
            for x in range(0, TUNING.screen_width, SWEEP_STRIDE)
            for y in range(0, TUNING.screen_height, SWEEP_STRIDE)
        }
        assert not swept & {*TUNING.tornado_colours, TUNING.tornado_warning_colour}


class TestDrawingAPausedFight:
    @staticmethod
    def test_the_pause_message_is_shown_while_paused() -> None:
        """Without this the game would freeze with no explanation of why."""
        pygame.font.init()
        font = pygame.font.Font(None, TUNING.label_font_size)
        frames = []
        for fight in (BossFight(paused=True), BossFight()):
            surface = pygame.Surface((TUNING.screen_width, TUNING.screen_height))
            draw_fight(surface, fight, font=font, message_font=font, bar_font=font)
            frames.append(pygame.image.tobytes(surface, "RGB"))

        assert frames[0] != frames[1]

    @staticmethod
    def test_the_pause_message_replaces_the_win_message() -> None:
        """Both messages sit in the middle of the screen, so only one of them can show.

        A won fight paused looks like a running fight paused everywhere but the boss, which
        turns red the moment it is beaten: same health bars, and the pause message rather
        than two cards printed over each other. The boss itself is left out of the sweep.
        """
        frames = [frame_of(BossFight(paused=True, state=state)) for state in (FightState.FIGHTING, FightState.WON)]

        around_the_boss = boss_box_at(TUNING.boss_centre)
        differences = [
            (x, y)
            for x in range(0, TUNING.screen_width, SWEEP_STRIDE)
            for y in range(0, TUNING.screen_height, SWEEP_STRIDE)
            if not around_the_boss.collidepoint(x, y) and colour_at(frames[0], (x, y)) != colour_at(frames[1], (x, y))
        ]
        assert differences == []


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


class TestHandleKey:
    @staticmethod
    def test_pressing_p_pauses_the_fight() -> None:
        fight = BossFight()

        handle_key(fight, pygame.K_p)

        assert fight.paused

    @staticmethod
    def test_pressing_backspace_unpauses_the_fight() -> None:
        fight = BossFight(paused=True)

        handle_key(fight, pygame.K_BACKSPACE)

        assert not fight.paused

    @staticmethod
    def test_pressing_p_again_leaves_the_fight_paused() -> None:
        """Only backspace unpauses, because only backspace is what the pause screen offers.

        A player who presses "p" twice out of habit reads the same instruction as before,
        rather than being dropped back into a fight they were not looking at.
        """
        fight = BossFight(paused=True)

        handle_key(fight, pygame.K_p)

        assert fight.paused

    @staticmethod
    def test_pressing_r_after_winning_starts_the_fight_again() -> None:
        fight = BossFight(boss_health=0, state=FightState.WON)

        handle_key(fight, pygame.K_r)

        assert fight.state is FightState.FIGHTING
        assert fight.boss_health == TUNING.boss_max_health

    @staticmethod
    def test_pressing_r_during_a_fight_does_nothing() -> None:
        """Replaying is only offered on the win screen, so a stray "r" cannot undo a fight."""
        fight = BossFight(boss_health=1)

        handle_key(fight, pygame.K_r)

        assert fight.boss_health == 1

    @staticmethod
    def test_pressing_r_while_paused_after_winning_does_not_restart_the_fight() -> None:
        """The pause screen covers the win screen, so it is not the replay prompt being read."""
        fight = BossFight(paused=True, boss_health=0, state=FightState.WON)

        handle_key(fight, pygame.K_r)

        assert fight.state is FightState.WON

    @staticmethod
    def test_pressing_any_other_key_does_nothing() -> None:
        fight = BossFight()

        handle_key(fight, pygame.K_SPACE)

        assert not fight.paused


class TestClickingWhilePaused:
    """The pause screen covers a live fight, so clicks through it have to be dropped."""

    @staticmethod
    def test_clicking_the_boss_while_paused_does_not_damage_it() -> None:
        fight = BossFight(paused=True)

        handle_click(fight, TUNING.boss_centre)

        assert fight.boss_health == TUNING.boss_max_health

    @staticmethod
    def test_clicking_the_dodge_button_while_paused_does_not_dodge() -> None:
        fight = BossFight(paused=True, dodge_window_left=TUNING.dodge_window_seconds)

        handle_click(fight, TUNING.dodge_button_centre)

        assert fight.attack_incoming
