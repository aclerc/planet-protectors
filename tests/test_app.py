from planet_protectors.app import handle_click
from planet_protectors.bossfight import BossFight, FightState
from planet_protectors.tuning import TUNING

EMPTY_SPACE = (40, 250)


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
