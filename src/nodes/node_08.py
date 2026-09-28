from __future__ import annotations

import time
from typing import Any, Dict
from src.base import AgentPayload, BaseAgent, register_node


@register_node("08")
class Node08BackendAudit(BaseAgent):
    """
    Unidad 08: Kōdo Senna.
    Especialidad: Auditoría de código, cumplimiento PEP 8 y análisis estático ligero.
    """

    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        start_time: float = time.perf_counter()
        raw_code: str = str(payload.data)

        lines = raw_code.splitlines()
        total_lines = len(lines)
        long_lines = sum(1 for line in lines if len(line) > 100)
        has_type_hints = "->" in raw_code or ":" in raw_code

        # Evaluación heurística simple
        clean = total_lines <= 50 and long_lines == 0 and has_type_hints

        verdict: Dict[str, Any] = {
            "node_name": "Kōdo Senna",
            "total_lines": total_lines,
            "pep8_long_line_violations": long_lines,
            "type_hints_detected": has_type_hints,
            "status": "APPROVED" if clean else "REFACTOR_REQUIRED",
            "message": "Código aceptable." if clean else "Violación de directivas PEP 8 o modularidad.",
        }

        # Estimación simple de tokens consumidos: 1 token por ~4 caracteres
        tokens: int = max(1, len(raw_code) // 4)

        return self.emit_success(data=verdict, start_time=start_time, tokens=tokens)
