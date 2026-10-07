import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.base import AgentPayload
from src.dispatcher import Dispatcher


class KernelExecutionError(Exception):
    """Excepción emitida cuando el Kernel detecta una falla en el flujo."""
    pass


class ChusuKanameKernel:
    """Kernel supervisor central de KAGAMI-Core con soporte de telemetría."""

    def __init__(
        self,
        dispatcher: Optional[Dispatcher] = None,
        max_total_tokens: int = 8192,
        max_total_time_ms: float = 30000.0,
        telemetry_path: Optional[str] = None,
    ) -> None:
        self.dispatcher = dispatcher or Dispatcher()
        self.max_total_tokens = max_total_tokens
        self.max_total_time_ms = max_total_time_ms
        self.telemetry_path = Path(telemetry_path) if telemetry_path else None
        self.execution_audit_log: List[Dict[str, Any]] = []

    def _persist_telemetry_entry(self, entry: Dict[str, Any]) -> None:
        """Escribe un registro atómico en el archivo de telemetría JSON Lines."""
        if not self.telemetry_path:
            return
        
        self.telemetry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.telemetry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def execute_pipeline(
        self, node_sequence: List[str], initial_payload: AgentPayload[Any]
    ) -> AgentPayload[Any]:
        """Ejecuta una secuencia ordenada de nodos encadenando sus resultados."""
        start_time: float = time.perf_counter()
        current_payload = initial_payload
        total_tokens = 0
        total_time_ms = 0.0

        for step_idx, node_id in enumerate(node_sequence):
            result_payload = self.dispatcher.dispatch(node_id, current_payload)

            step_tokens = result_payload.tokens_consumed
            step_time = result_payload.execution_time_ms
            total_tokens += step_tokens
            total_time_ms += step_time

            self.execution_audit_log.append({
                "step": step_idx + 1,
                "node_id": node_id,
                "execution_time_ms": step_time,
                "tokens_consumed": step_tokens,
                "status": result_payload.metadata.get("status", "unknown"),
            })

            if result_payload.metadata.get("status") == "error":
                raise KernelExecutionError(
                    f"Falla en Kernel al ejecutar paso {step_idx + 1} (Nodo {node_id}): "
                    f"{result_payload.metadata.get('error_message')}"
                )

            if total_tokens > self.max_total_tokens:
                raise KernelExecutionError(
                    f"Presupuesto de tokens excedido en el Kernel: {total_tokens} > {self.max_total_tokens}"
                )

            current_payload = result_payload

        kernel_elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        current_payload.metadata["kernel_supervisor"] = "Chūsu Kaname"
        current_payload.metadata["pipeline_length"] = len(node_sequence)
        current_payload.metadata["total_pipeline_time_ms"] = round(kernel_elapsed_ms, 3)
        current_payload.metadata["total_tokens_consumed"] = total_tokens

        # Persistir la traza completa
        telemetry_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "supervisor": "Chūsu Kaname",
            "pipeline": node_sequence,
            "total_time_ms": round(kernel_elapsed_ms, 3),
            "total_tokens": total_tokens,
            "steps": list(self.execution_audit_log),
        }
        self._persist_telemetry_entry(telemetry_record)

        return current_payload
