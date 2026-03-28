"""Simple priority engine scaffold for future APL logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class CombatState:
    target_in_range: bool = True
    holy_power: int = 0
    cooldown_ready: bool = False


class LogicEngine:
    """Evaluates a minimal priority list and returns the next suggested action."""

    def __init__(self, priorities: Iterable[str] | None = None) -> None:
        self.priorities = list(priorities or ["cooldown", "spender", "builder", "wait"])

    def next_action(self, state: CombatState) -> str:
        if not state.target_in_range:
            return "wait"
        if state.cooldown_ready and "cooldown" in self.priorities:
            return "cooldown"
        if state.holy_power >= 3 and "spender" in self.priorities:
            return "spender"
        if "builder" in self.priorities:
            return "builder"
        return "wait"

