from __future__ import annotations

import time
from typing import Any, Dict
from src.base import AgentPayload, BaseAgent, register_node


@register_node("04")
class Node04GachaRisk(BaseAgent):
    """
    Unidad 04: Shisū Sumire.
    Especialidad: Modelado de probabilidad estocástica y cálculo de riesgo/pity.
    """

    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        start_time: float = time.perf_counter()
        input_data: Dict[str, Any] = payload.data if isinstance(payload.data, dict) else {}

        # Extracción de parámetros con validación dura
        base_rate: float = float(input_data.get("base_rate", 0.006))  # 0.6% típico
        pulls: int = int(input_data.get("pulls", 1))

        if not (0.0 < base_rate <= 1.0):
            raise ValueError("base_rate debe estar en el rango (0.0, 1.0].")
        if pulls < 1:
            raise ValueError("pulls debe ser al menos 1.")

        # Probabilidad de no sacar nada en N tiradas: (1 - p)^n
        p_failure: float = (1.0 - base_rate) ** pulls
        p_success: float = 1.0 - p_failure

        result: Dict[str, Any] = {
            "node_name": "Shisū Sumire",
            "base_rate": base_rate,
            "pulls_evaluated": pulls,
            "cumulative_success_probability": round(p_success, 4),
            "expected_pulls_to_guarantee": int(1.0 / base_rate),
        }

        return self.emit_success(data=result, start_time=start_time, tokens=12)
