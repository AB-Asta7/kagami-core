import random
import time
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from src.base import BaseAgent, AgentPayload, register_node


class FSMState(Enum):
    BASE_RATE = auto()
    SOFT_PITY = auto()
    HARD_PITY = auto()


@register_node("05")
class Node05GachaFSM(BaseAgent):
    """Nodo del orquestador KAGAMI para simulación de gacha basada en FSM."""

    def __init__(self, max_context_tokens: int = 2048) -> None:
        super().__init__(max_context_tokens=max_context_tokens)

    def _evaluate_pull(
        self,
        current_pull: int,
        base_rate: float,
        soft_pity_start: int,
        hard_pity: int,
        pity_increment: float,
        rng: random.Random,
    ) -> bool:
        if current_pull >= hard_pity:
            return True

        if current_pull >= soft_pity_start:
            rate = base_rate + (current_pull - soft_pity_start + 1) * pity_increment
        else:
            rate = base_rate

        return rng.random() < min(rate, 1.0)

    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        start_time: float = time.perf_counter()

        data: Dict[str, Any] = payload.data or {}
        base_rate: float = float(data.get("base_rate", 0.006))
        soft_pity_start: int = int(data.get("soft_pity_start", 74))
        hard_pity: int = int(data.get("hard_pity", 90))
        pity_increment: float = float(data.get("pity_increment", 0.06))
        target_pulls: int = int(data.get("target_pulls", 90))
        has_guaranteed: bool = bool(data.get("has_guaranteed", False))
        seed: Optional[int] = data.get("seed")

        rng = random.Random(seed) if seed is not None else random.Random()

        pity_counter = 0
        banner_guaranteed = has_guaranteed
        obtained_5_stars: List[Dict[str, Any]] = []

        for pull_idx in range(1, target_pulls + 1):
            pity_counter += 1
            got_5_star = self._evaluate_pull(
                current_pull=pity_counter,
                base_rate=base_rate,
                soft_pity_start=soft_pity_start,
                hard_pity=hard_pity,
                pity_increment=pity_increment,
                rng=rng,
            )

            if got_5_star:
                if banner_guaranteed:
                    is_promotional = True
                    banner_guaranteed = False
                else:
                    won_50_50 = rng.random() < 0.5
                    is_promotional = won_50_50
                    banner_guaranteed = not won_50_50

                obtained_5_stars.append({
                    "pull_number": pull_idx,
                    "pity_count": pity_counter,
                    "is_promotional": is_promotional,
                })
                pity_counter = 0

        elapsed_ms: float = (time.perf_counter() - start_time) * 1000.0

        result_data = {
            "node_name": "Gacha FSM Simulator",
            "total_pulls": target_pulls,
            "total_5_stars": len(obtained_5_stars),
            "promotional_count": sum(1 for item in obtained_5_stars if item["is_promotional"]),
            "guaranteed_active_next": banner_guaranteed,
            "items": obtained_5_stars,
        }

        return AgentPayload(
            node_id="05",
            execution_time_ms=round(elapsed_ms, 3),
            tokens_consumed=len(obtained_5_stars) * 4,
            data=result_data,
            metadata={"status": "success"},
        )
