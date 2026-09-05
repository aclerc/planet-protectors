import random
from itertools import pairwise

from planet_protectors.bossfight import BossFight, FightState, Tornado
from planet_protectors.tuning import TUNING

# Nudge past event boundaries so a test never depends on whether an event scheduled for
# exactly now has fired yet.
A_MOMENT = 0.1

# One frame at the game's frame rate, and a minute of them: long enough for the boss to
# reach several of the places it drifts to.
A_FRAME = 1 / 60
A_LONG_DRIFT = 60 * 60

# Longer than it takes Pina to walk the whole width of the screen.
A_LONG_WALK = 10.0


def advance(fight: BossFight, seconds: float, *, step: float = 1 / 60) -> None:
    """Run the fight forward by roughly the given number of seconds."""
    elapsed = 0.0
    while elapsed < seconds:
        fight.tick(step)
        elapsed += step


class TestHittingTheBoss:
    @staticmethod
    def test_enough_hits_defeats_the_boss() -> None:
        fight = BossFight()

        for _ in range(TUNING.boss_max_health // TUNING.hit_damage):
            fight.hit_boss()

        assert fight.boss_health == 0
        assert fight.state is FightState.WON

    @staticmethod
    def test_boss_health_never_falls_below_zero() -> None:
        fight = BossFight(boss_health=5)

        fight.hit_boss(damage=999)

        assert fight.boss_health == 0

    @staticmethod
    def test_hits_after_winning_are_ignored() -> None:
        fight = BossFight(boss_health=TUNING.hit_damage)
        fight.hit_boss()

        fight.hit_boss()

        assert fight.state is FightState.WON
        assert fight.boss_health == 0


class TestTheDefeatedBoss:
    """The boss turns red and fades off the planet once it is beaten.

    The fade is what tells a five-year-old the fight is over, so it is state the fight owns
    rather than an animation the window invents: pausing freezes it like everything else.
    """

    @staticmethod
    def test_the_boss_is_solid_while_it_is_still_fighting() -> None:
        fight = BossFight()

        advance(fight, 1.0)

        assert fight.boss_opacity == 1.0
        assert not fight.boss_vanished

    @staticmethod
    def test_the_boss_is_still_there_the_moment_it_is_beaten() -> None:
        fight = BossFight()

        fight.hit_boss(damage=TUNING.boss_max_health)

        assert fight.boss_opacity == 1.0
        assert not fight.boss_vanished

    @staticmethod
    def test_the_beaten_boss_fades_as_the_fight_carries_on_ticking() -> None:
        fight = BossFight()
        fight.hit_boss(damage=TUNING.boss_max_health)

        advance(fight, TUNING.boss_vanish_seconds / 2)

        assert 0 < fight.boss_opacity < 1
        assert not fight.boss_vanished

    @staticmethod
    def test_the_beaten_boss_is_gone_once_it_has_finished_fading() -> None:
        fight = BossFight()
        fight.hit_boss(damage=TUNING.boss_max_health)

        advance(fight, TUNING.boss_vanish_seconds + A_MOMENT)

        assert fight.boss_opacity == 0
        assert fight.boss_vanished

    @staticmethod
    def test_pausing_holds_the_fading_boss_where_it_is() -> None:
        fight = BossFight()
        fight.hit_boss(damage=TUNING.boss_max_health)
        advance(fight, TUNING.boss_vanish_seconds / 2)
        faded_to = fight.boss_opacity

        fight.pause()
        advance(fight, TUNING.boss_vanish_seconds)

        assert fight.boss_opacity == faded_to

    @staticmethod
    def test_restarting_brings_the_boss_back() -> None:
        fight = BossFight()
        fight.hit_boss(damage=TUNING.boss_max_health)
        advance(fight, TUNING.boss_vanish_seconds + A_MOMENT)

        fight.restart()

        assert fight.boss_opacity == 1.0
        assert not fight.boss_vanished


class TestBossAttacks:
    @staticmethod
    def test_no_attack_is_incoming_at_the_start() -> None:
        fight = BossFight()

        assert not fight.attack_incoming

    @staticmethod
    def test_the_boss_telegraphs_an_attack_after_the_attack_interval() -> None:
        fight = BossFight()

        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)

        assert fight.attack_incoming

    @staticmethod
    def test_the_boss_attacks_again_after_an_attack_resolves() -> None:
        fight = BossFight()
        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)
        fight.dodge()
        assert not fight.attack_incoming

        advance(fight, TUNING.seconds_between_attacks)

        assert fight.attack_incoming


class TestDodging:
    @staticmethod
    def test_dodging_an_incoming_attack_avoids_damage() -> None:
        fight = BossFight()
        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)

        fight.dodge()
        advance(fight, TUNING.dodge_window_seconds)

        assert fight.pina_health == TUNING.pina_max_health

    @staticmethod
    def test_dodging_an_incoming_attack_reports_that_it_landed() -> None:
        fight = BossFight()
        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)

        assert fight.dodge() is True

    @staticmethod
    def test_missing_the_dodge_window_costs_health() -> None:
        fight = BossFight()

        advance(fight, TUNING.seconds_between_attacks + TUNING.dodge_window_seconds + A_MOMENT)

        assert fight.pina_health == TUNING.pina_max_health - TUNING.attack_damage

    @staticmethod
    def test_dodging_when_nothing_is_incoming_does_nothing() -> None:
        fight = BossFight()

        assert fight.dodge() is False
        assert fight.pina_health == TUNING.pina_max_health


class TestLosingAndRetrying:
    @staticmethod
    def test_running_out_of_health_loses_the_fight() -> None:
        fight = BossFight(pina_health=TUNING.attack_damage)

        advance(fight, TUNING.seconds_between_attacks + TUNING.dodge_window_seconds + A_MOMENT)

        assert fight.pina_health == 0
        assert fight.state is FightState.LOST

    @staticmethod
    def test_a_lost_fight_restarts_at_full_health_after_the_retry_delay() -> None:
        fight = BossFight(pina_health=TUNING.attack_damage)
        advance(fight, TUNING.seconds_between_attacks + TUNING.dodge_window_seconds + A_MOMENT)
        assert fight.state is FightState.LOST

        advance(fight, TUNING.retry_delay_seconds + A_MOMENT)

        assert fight.state is FightState.FIGHTING
        assert fight.pina_health == TUNING.pina_max_health
        assert fight.boss_health == TUNING.boss_max_health

    @staticmethod
    def test_the_boss_does_not_attack_while_the_fight_is_lost() -> None:
        fight = BossFight(pina_health=TUNING.attack_damage)
        advance(fight, TUNING.seconds_between_attacks + TUNING.dodge_window_seconds + A_MOMENT)

        advance(fight, TUNING.retry_delay_seconds / 2)

        assert fight.state is FightState.LOST
        assert fight.pina_health == 0


class TestBossMovement:
    @staticmethod
    def test_the_boss_drifts_away_from_where_it_started() -> None:
        fight = BossFight(rng=random.Random(1))

        advance(fight, 1.0)

        assert fight.boss_centre != TUNING.boss_centre

    @staticmethod
    def test_the_boss_stays_fully_on_screen() -> None:
        """The whole raccoon has to stay in the window, ear tips and feet included.

        Nothing else complains if it wanders off: the fight carries on, and a boss that is
        half off the edge can still be clicked, so a playtest can easily miss it.
        """
        fight = BossFight(rng=random.Random(2))
        margin_x, margin_y = TUNING.boss_roam_margin

        for _ in range(A_LONG_DRIFT):
            fight.tick(A_FRAME)
            x, y = fight.boss_centre
            assert margin_x <= x <= TUNING.screen_width - margin_x
            assert margin_y <= y <= TUNING.screen_height - margin_y

    @staticmethod
    def test_the_boss_keeps_picking_new_places_to_drift_to() -> None:
        """Without this the boss reaches its first target and parks there for good."""
        fight = BossFight(rng=random.Random(3))

        targets = set()
        for _ in range(A_LONG_DRIFT):
            fight.tick(A_FRAME)
            targets.add(fight.boss_target)

        assert len(targets) > 1

    @staticmethod
    def test_the_boss_holds_still_once_the_fight_is_won() -> None:
        fight = BossFight(rng=random.Random(4))
        advance(fight, 1.0)
        fight.hit_boss(damage=TUNING.boss_max_health)
        settled = fight.boss_centre

        advance(fight, 1.0)

        assert fight.boss_centre == settled

    @staticmethod
    def test_the_boss_holds_still_while_the_fight_is_lost() -> None:
        fight = BossFight(pina_health=TUNING.attack_damage, rng=random.Random(5))
        advance(fight, TUNING.seconds_between_attacks + TUNING.dodge_window_seconds + A_MOMENT)
        settled = fight.boss_centre

        advance(fight, TUNING.retry_delay_seconds / 2)

        assert fight.state is FightState.LOST
        assert fight.boss_centre == settled

    @staticmethod
    def test_restarting_puts_the_boss_back_where_it_began() -> None:
        fight = BossFight(rng=random.Random(6))
        advance(fight, 1.0)

        fight.restart()

        assert fight.boss_centre == TUNING.boss_centre


class TestPinaMovement:
    @staticmethod
    def test_holding_right_walks_pina_right() -> None:
        fight = BossFight()

        fight.steer_pina(1)
        advance(fight, 1.0)

        assert fight.pina_centre[0] > TUNING.pina_centre[0]

    @staticmethod
    def test_holding_left_walks_pina_left() -> None:
        fight = BossFight()

        fight.steer_pina(-1)
        advance(fight, 1.0)

        assert fight.pina_centre[0] < TUNING.pina_centre[0]

    @staticmethod
    def test_pina_walks_sideways_only() -> None:
        fight = BossFight()

        fight.steer_pina(1)
        advance(fight, 1.0)

        assert fight.pina_centre[1] == TUNING.pina_centre[1]

    @staticmethod
    def test_pina_stops_when_the_key_is_released() -> None:
        fight = BossFight()
        fight.steer_pina(1)
        advance(fight, 0.5)
        walked_to = fight.pina_centre

        fight.steer_pina(0)
        advance(fight, 0.5)

        assert fight.pina_centre == walked_to

    @staticmethod
    def test_pina_cannot_be_walked_off_either_edge() -> None:
        """Pina reaches the edge long before the player lets go of the key.

        A blob half off the screen is the first thing a five-year-old will try, and nothing
        else in the game stops it happening.
        """
        fight = BossFight()

        fight.steer_pina(-1)
        advance(fight, A_LONG_WALK)
        assert fight.pina_centre[0] == TUNING.pina_roam_margin

        fight.steer_pina(1)
        advance(fight, A_LONG_WALK)
        assert fight.pina_centre[0] == TUNING.screen_width - TUNING.pina_roam_margin

    @staticmethod
    def test_pina_holds_still_once_the_fight_is_won() -> None:
        fight = BossFight()
        fight.steer_pina(1)
        advance(fight, 0.5)
        fight.hit_boss(damage=TUNING.boss_max_health)
        stopped = fight.pina_centre

        advance(fight, 1.0)

        assert fight.pina_centre == stopped

    @staticmethod
    def test_restarting_puts_pina_back_where_he_began() -> None:
        fight = BossFight()
        fight.steer_pina(-1)
        advance(fight, 1.0)

        fight.restart()

        assert fight.pina_centre == TUNING.pina_centre
        assert fight.pina_direction == 0


class TestPausing:
    """Pausing freezes the whole fight until the player asks for it back."""

    @staticmethod
    def test_a_fight_starts_unpaused() -> None:
        fight = BossFight()

        assert not fight.paused

    @staticmethod
    def test_pausing_holds_the_boss_where_it_is() -> None:
        fight = BossFight()
        advance(fight, A_MOMENT)
        held_at = fight.boss_centre

        fight.pause()
        advance(fight, A_LONG_DRIFT)

        assert fight.boss_centre == held_at

    @staticmethod
    def test_pausing_holds_pina_where_he_is() -> None:
        fight = BossFight()
        fight.steer_pina(1)
        advance(fight, A_MOMENT)
        held_at = fight.pina_centre

        fight.pause()
        advance(fight, A_LONG_WALK)

        assert fight.pina_centre == held_at

    @staticmethod
    def test_the_boss_does_not_start_an_attack_while_paused() -> None:
        fight = BossFight()

        fight.pause()
        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)

        assert not fight.attack_incoming

    @staticmethod
    def test_an_incoming_attack_does_not_land_while_paused() -> None:
        fight = BossFight()
        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)
        assert fight.attack_incoming

        fight.pause()
        advance(fight, TUNING.dodge_window_seconds + A_MOMENT)

        assert fight.pina_health == TUNING.pina_max_health

    @staticmethod
    def test_a_lost_fight_does_not_restart_while_paused() -> None:
        fight = BossFight(pina_health=0, state=FightState.LOST, seconds_to_retry=TUNING.retry_delay_seconds)

        fight.pause()
        advance(fight, TUNING.retry_delay_seconds + A_MOMENT)

        assert fight.state is FightState.LOST

    @staticmethod
    def test_resuming_lets_the_fight_carry_on() -> None:
        fight = BossFight()
        fight.pause()
        advance(fight, A_LONG_DRIFT)

        fight.resume()
        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)

        assert not fight.paused
        assert fight.attack_incoming

    @staticmethod
    def test_the_dodge_window_still_has_its_time_left_after_a_pause() -> None:
        fight = BossFight()
        advance(fight, TUNING.seconds_between_attacks + A_MOMENT)
        left_when_paused = fight.dodge_window_left

        fight.pause()
        advance(fight, TUNING.dodge_window_seconds)

        assert fight.dodge_window_left == left_when_paused


class TestTornadoes:
    """A tornado marks the ground it will land on, grows, wanders, and blows itself out."""

    @staticmethod
    def test_no_tornado_is_on_the_planet_at_the_start() -> None:
        fight = BossFight()

        assert fight.tornado is None

    @staticmethod
    def test_a_tornado_appears_after_the_gap_between_them() -> None:
        fight = BossFight()

        advance(fight, TUNING.seconds_between_tornadoes + A_MOMENT)

        assert fight.tornado is not None

    @staticmethod
    def test_a_tornado_is_only_a_warning_when_it_first_appears() -> None:
        """The orange circle has to come first, or there is nothing to get out of the way of."""
        fight = BossFight()

        advance(fight, TUNING.seconds_between_tornadoes + A_MOMENT)

        assert fight.tornado is not None
        assert not fight.tornado.landed

    @staticmethod
    def test_a_tornado_lands_once_its_warning_runs_out() -> None:
        fight = BossFight(tornado=Tornado(x=TUNING.pina_centre[0]))

        advance(fight, TUNING.tornado_warning_seconds + A_MOMENT)

        assert fight.tornado is not None
        assert fight.tornado.landed

    @staticmethod
    def test_a_warning_on_top_of_pina_does_not_hurt_her() -> None:
        fight = BossFight(tornado=Tornado(x=TUNING.pina_centre[0]))

        advance(fight, TUNING.tornado_warning_seconds - A_MOMENT)

        assert fight.pina_health == TUNING.pina_max_health

    @staticmethod
    def test_a_tornado_starts_small_and_grows() -> None:
        fight = BossFight(tornado=Tornado(x=800, seconds_to_land=0.0))
        assert fight.tornado is not None
        started_at = fight.tornado.radius

        advance(fight, TUNING.tornado_life_seconds / 2)

        assert fight.tornado is not None
        assert started_at == TUNING.tornado_start_radius
        assert fight.tornado.radius > started_at

    @staticmethod
    def test_a_tornado_blows_itself_out_within_its_five_seconds() -> None:
        fight = BossFight(tornado=Tornado(x=800, seconds_to_land=0.0))

        advance(fight, TUNING.tornado_life_seconds + A_MOMENT)

        assert fight.tornado is None

    @staticmethod
    def test_another_tornado_follows_the_one_that_blew_out() -> None:
        fight = BossFight(tornado=Tornado(x=800, seconds_to_land=0.0))
        advance(fight, TUNING.tornado_life_seconds + A_MOMENT)
        assert fight.tornado is None

        advance(fight, TUNING.seconds_between_tornadoes + A_MOMENT)

        assert fight.tornado is not None

    @staticmethod
    def test_a_tornado_wanders_both_ways_across_the_planet() -> None:
        """It drifts on its own rather than chasing Pina, so walking away always works."""
        fight = BossFight(tornado=Tornado(x=480, seconds_to_land=0.0), rng=random.Random(7))
        assert fight.tornado is not None
        columns = []
        for _ in range(round(TUNING.tornado_life_seconds / A_FRAME) - 1):
            fight.tick(A_FRAME)
            assert fight.tornado is not None
            columns.append(fight.tornado.x)

        steps = [later - earlier for earlier, later in pairwise(columns)]
        assert any(step > 0 for step in steps)
        assert any(step < 0 for step in steps)

    @staticmethod
    def test_a_tornado_stays_on_the_screen() -> None:
        fight = BossFight(tornado=Tornado(x=TUNING.tornado_roam_margin, seconds_to_land=0.0), rng=random.Random(3))

        for _ in range(round(TUNING.tornado_life_seconds / A_FRAME) - 1):
            fight.tick(A_FRAME)
            assert fight.tornado is not None
            assert 0 <= fight.tornado.x <= TUNING.screen_width

    @staticmethod
    def test_a_tornado_hurts_pina_when_it_touches_her() -> None:
        fight = BossFight(tornado=Tornado(x=TUNING.pina_centre[0], seconds_to_land=0.0))

        advance(fight, A_MOMENT)

        assert fight.pina_health == TUNING.pina_max_health - TUNING.tornado_damage

    @staticmethod
    def test_a_tornado_that_has_hit_pina_cannot_hurt_her_again() -> None:
        """One hit per tornado, so a tornado that parks on Pina cannot finish the fight on its own."""
        fight = BossFight(tornado=Tornado(x=TUNING.pina_centre[0], seconds_to_land=0.0))

        advance(fight, TUNING.tornado_life_seconds - A_MOMENT)

        assert fight.pina_health == TUNING.pina_max_health - TUNING.tornado_damage

    @staticmethod
    def test_a_tornado_across_the_planet_leaves_pina_alone() -> None:
        fight = BossFight(tornado=Tornado(x=TUNING.screen_width - TUNING.tornado_roam_margin, seconds_to_land=0.0))

        advance(fight, A_MOMENT)

        assert fight.pina_health == TUNING.pina_max_health

    @staticmethod
    def test_walking_out_of_the_way_saves_pina() -> None:
        fight = BossFight(tornado=Tornado(x=TUNING.pina_centre[0] + 200, seconds_to_land=0.0, drift=-1))
        fight.steer_pina(-1)

        advance(fight, A_FRAME)

        assert fight.pina_health == TUNING.pina_max_health

    @staticmethod
    def test_a_tornado_holds_still_while_the_fight_is_paused() -> None:
        fight = BossFight(tornado=Tornado(x=800, seconds_to_land=0.0))
        assert fight.tornado is not None
        held_at = (fight.tornado.x, fight.tornado.radius)

        fight.pause()
        advance(fight, TUNING.tornado_life_seconds + A_MOMENT)

        assert fight.tornado is not None
        assert (fight.tornado.x, fight.tornado.radius) == held_at

    @staticmethod
    def test_restarting_blows_the_tornado_away() -> None:
        fight = BossFight(tornado=Tornado(x=800, seconds_to_land=0.0))

        fight.restart()

        assert fight.tornado is None
