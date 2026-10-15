import json
import time
from pathlib import Path
from typing import Any, Dict, List
from src.base import AgentPayload, KernelExecutionError
from src.dispatcher import Dispatcher


class ChusuKanameKernel:
    """Kernel supervisor KAGAMI: control de ejecución, presupuestos y telemetría."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        telemetry_path: str = "logs/telemetry.jsonl",
        max_total_time_ms: float = 30000.0,
        max_total_tokens: int = 8192,
    ) -> None:
        self.dispatcher = dispatcher
        self.telemetry_path = Path(telemetry_path)
        self.telemetry_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_total_time_ms = max_total_time_ms
        self.max_total_tokens = max_total_tokens
        self.execution_audit_log: List[Dict[str, Any]] = []

    def _persist_telemetry_entry(self, entry: Dict[str, Any]) -> None:
        with open(self.telemetry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def execute_pipeline(
        self,
        node_sequence: List[str],
        initial_payload: AgentPayload[Any],
    ) -> AgentPayload[Any]:
        pipeline_start: float = time.perf_counter()
        accumulated_time_ms: float = 0.0
        accumulated_tokens: int = 0
        self.execution_audit_log = []
        current_payload = initial_payload

        for node_id in node_sequence:
            step_start = time.perf_counter()
            try:
                result_payload = self.dispatcher.dispatch(node_id, current_payload)
            except Exception as e:
                step_elapsed = (time.perf_counter() - step_start) * 1000.0
                accumulated_time_ms += step_elapsed
                total_pipeline_time = (time.perf_counter() - pipeline_start) * 1000.0

                failure_entry = {
                    "timestamp": time.time(),
                    "status": "failed",
                    "supervisor": "Chūsu Kaname",
                    "kernel_supervisor": "Chūsu Kaname",
                    "failed_node": node_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "pipeline": node_sequence,
                    "pipeline_length": len(node_sequence),
                    "total_tokens": accumulated_tokens,
                    "total_tokens_consumed": accumulated_tokens,
                    "accumulated_tokens": accumulated_tokens,
                    "total_pipeline_time_ms": round(total_pipeline_time, 3),
                    "steps": self.execution_audit_log,
                    "audit_log": self.execution_audit_log,
                }
                self._persist_telemetry_entry(failure_entry)
                raise KernelExecutionError(f"Fallo en nodo '{node_id}': {e}") from e

            step_elapsed = (time.perf_counter() - step_start) * 1000.0
            accumulated_time_ms += result_payload.execution_time_ms or step_elapsed
            accumulated_tokens += result_payload.tokens_consumed

            self.execution_audit_log.append({
                "node_id": node_id,
                "execution_time_ms": result_payload.execution_time_ms,
                "tokens_consumed": result_payload.tokens_consumed,
            })

            if accumulated_tokens > self.max_total_tokens:
                raise KernelExecutionError(
                    f"Presupuesto de tokens excedido: {accumulated_tokens} > {self.max_total_tokens}"
                )

            total_elapsed_now = (time.perf_counter() - pipeline_start) * 1000.0
            if total_elapsed_now > self.max_total_time_ms:
                raise KernelExecutionError(
                    f"Presupuesto de tiempo excedido: {total_elapsed_now:.2f}ms > {self.max_total_time_ms}ms"
                )

            current_payload = result_payload

        total_pipeline_time_ms = (time.perf_counter() - pipeline_start) * 1000.0

        telemetry_entry = {
            "timestamp": time.time(),
            "status": "success",
            "supervisor": "Chūsu Kaname",
            "kernel_supervisor": "Chūsu Kaname",
            "pipeline": node_sequence,
            "pipeline_length": len(node_sequence),
            "total_nodes_executed": len(node_sequence),
            "total_tokens": accumulated_tokens,
            "total_tokens_consumed": accumulated_tokens,
            "total_pipeline_time_ms": round(total_pipeline_time_ms, 3),
            "steps": self.execution_audit_log,
            "audit_log": self.execution_audit_log,
        }
        self._persist_telemetry_entry(telemetry_entry)

        updated_metadata = dict(current_payload.metadata) if current_payload.metadata else {}
        updated_metadata.update({
            "supervisor": "Chūsu Kaname",
            "kernel_supervisor": "Chūsu Kaname",
            "pipeline_length": len(node_sequence),
            "total_pipeline_time_ms": round(total_pipeline_time_ms, 3),
            "total_tokens": accumulated_tokens,
            "total_tokens_consumed": accumulated_tokens,
            "pipeline_nodes": node_sequence,
        })

        return current_payload.model_copy(update={"metadata": updated_metadata})
