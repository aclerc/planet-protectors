"""The boss fight rules.

Nothing here draws anything or reads a clock. `tick` advances the fight by a time step
supplied by the caller, so a whole fight can be played out in a test without a window.
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto

from planet_protectors.tuning import TUNING, Point


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
    paused: bool = False
    seconds_to_next_attack: float = TUNING.seconds_between_attacks
    dodge_window_left: float = 0.0
    seconds_to_retry: float = 0.0
    boss_x: float = TUNING.boss_centre[0]
    boss_y: float = TUNING.boss_centre[1]
    boss_target: Point = TUNING.boss_centre
    pina_x: float = TUNING.pina_centre[0]
    pina_direction: int = 0
    rng: random.Random = field(default_factory=random.Random)

    @property
    def pina_centre(self) -> Point:
        """Where Pina has walked to; he only moves sideways."""
        return (round(self.pina_x), TUNING.pina_centre[1])

    @property
    def boss_centre(self) -> Point:
        """Where the boss has drifted to, in whole pixels."""
        return (round(self.boss_x), round(self.boss_y))

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

    def steer_pina(self, direction: int) -> None:
        """Set which way the player is walking Pina: -1 for left, 1 for right, 0 for still."""
        self.pina_direction = direction

    def pause(self) -> None:
        """Freeze the fight until `resume` is called."""
        self.paused = True

    def resume(self) -> None:
        """Let a paused fight carry on from where it stopped."""
        self.paused = False

    def tick(self, dt: float) -> None:
        """Advance the fight by `dt` seconds, unless it is paused."""
        if self.paused:
            return

        if self.state is FightState.LOST:
            self.seconds_to_retry -= dt
            if self.seconds_to_retry <= 0:
                self.restart()
            return

        if self.state is not FightState.FIGHTING:
            return

        self._drift(dt)
        self._walk(dt)

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
        self.boss_x, self.boss_y = TUNING.boss_centre
        self.boss_target = TUNING.boss_centre
        self.pina_x = TUNING.pina_centre[0]
        self.pina_direction = 0

    def _drift(self, dt: float) -> None:
        step = TUNING.boss_speed * dt
        towards = (self.boss_target[0] - self.boss_x, self.boss_target[1] - self.boss_y)
        distance = math.hypot(*towards)
        if distance <= step:
            self.boss_x, self.boss_y = self.boss_target
            self.boss_target = self._somewhere_to_drift_to()
            return
        self.boss_x += towards[0] / distance * step
        self.boss_y += towards[1] / distance * step

    def _walk(self, dt: float) -> None:
        walked = self.pina_x + self.pina_direction * TUNING.pina_speed * dt
        self.pina_x = min(max(walked, TUNING.pina_roam_margin), TUNING.screen_width - TUNING.pina_roam_margin)

    def _somewhere_to_drift_to(self) -> Point:
        margin_x, margin_y = TUNING.boss_roam_margin
        return (
            self.rng.randint(margin_x, TUNING.screen_width - margin_x),
            self.rng.randint(margin_y, TUNING.screen_height - margin_y),
        )

    def _take_hit(self) -> None:
        self.pina_health = max(0, self.pina_health - TUNING.attack_damage)
        if self.pina_health == 0:
            self.state = FightState.LOST
            self.seconds_to_retry = TUNING.retry_delay_seconds
