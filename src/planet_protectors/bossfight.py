"""The boss fight rules.

Nothing here draws anything or reads a clock. `tick` advances the fight by a time step
supplied by the caller, so a whole fight can be played out in a test without a window.
"""

from dataclasses import dataclass
from enum import Enum, auto

from planet_protectors.tuning import TUNING


class FightState(Enum):
    """Whether the fight is running, won, or paused after a loss before restarting."""

    FIGHTING = auto()
    WON = auto()
    LOST = auto()


@dataclass
class BossFight:
    """One boss fight: click the boss to damage it, dodge the attacks it sends back."""

    boss_health: int = TUNING.boss_max_health
    pina_health: int = TUNING.pina_max_health
    state: FightState = FightState.FIGHTING
    seconds_to_next_attack: float = TUNING.seconds_between_attacks
    dodge_window_left: float = 0.0
    seconds_to_retry: float = 0.0

    @property
    def attack_incoming(self) -> bool:
        """Whether an attack is telegraphed and can still be dodged."""
        return self.dodge_window_left > 0

    def hit_boss(self, *, damage: int = TUNING.hit_damage) -> None:
        """Damage the boss, winning the fight once its health reaches zero."""
        if self.state is not FightState.FIGHTING:
            return
        self.boss_health = max(0, self.boss_health - damage)
        if self.boss_health == 0:
            self.state = FightState.WON

    def dodge(self) -> bool:
        """Dodge an incoming attack, returning whether there was one to dodge."""
        if not self.attack_incoming:
            return False
        self.dodge_window_left = 0.0
        self.seconds_to_next_attack = TUNING.seconds_between_attacks
        return True

    def tick(self, dt: float) -> None:
        """Advance the fight by `dt` seconds."""
        if self.state is FightState.LOST:
            self.seconds_to_retry -= dt
            if self.seconds_to_retry <= 0:
                self.restart()
            return

        if self.state is not FightState.FIGHTING:
            return

        if self.attack_incoming:
            self.dodge_window_left -= dt
            if self.dodge_window_left <= 0:
                self.dodge_window_left = 0.0
                self._take_hit()
            return

        self.seconds_to_next_attack -= dt
        if self.seconds_to_next_attack <= 0:
            self.seconds_to_next_attack = TUNING.seconds_between_attacks
            self.dodge_window_left = TUNING.dodge_window_seconds

    def restart(self) -> None:
        """Put the fight back to its opening state at full health."""
        self.boss_health = TUNING.boss_max_health
        self.pina_health = TUNING.pina_max_health
        self.state = FightState.FIGHTING
        self.seconds_to_next_attack = TUNING.seconds_between_attacks
        self.dodge_window_left = 0.0
        self.seconds_to_retry = 0.0

    def _take_hit(self) -> None:
        self.pina_health = max(0, self.pina_health - TUNING.attack_damage)
        if self.pina_health == 0:
            self.state = FightState.LOST
            self.seconds_to_retry = TUNING.retry_delay_seconds
