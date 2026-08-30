from planet_protectors.bossfight import BossFight, FightState
from planet_protectors.tuning import TUNING

# Nudge past event boundaries so a test never depends on whether an event scheduled for
# exactly now has fired yet.
A_MOMENT = 0.1


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
