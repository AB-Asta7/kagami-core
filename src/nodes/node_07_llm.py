import time
from typing import Any, Optional
from src.base import BaseAgent, AgentPayload, register_node
from src.clients.gemini_client import GeminiAdapter


@register_node("07")
class Node07LLM(BaseAgent):
    """Nodo del orquestador KAGAMI para inferencia con modelos Gemini."""

    def __init__(self, max_context_tokens: int = 4096, adapter: Optional[GeminiAdapter] = None) -> None:
        super().__init__(max_context_tokens=max_context_tokens)
        self.adapter = adapter or GeminiAdapter()

    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        start_time: float = time.perf_counter()

        if isinstance(payload.data, dict):
            prompt = payload.data.get("prompt")
            system_instruction = payload.data.get("system_instruction")
        elif isinstance(payload.data, str):
            prompt = payload.data
            system_instruction = None
        else:
            raise ValueError("El payload.data debe ser un string o un dict con la clave 'prompt'.")

        if not prompt or not isinstance(prompt, str):
            raise ValueError("El campo 'prompt' no puede estar vacío.")

        response = self.adapter.generate(prompt=prompt, system_instruction=system_instruction)
        elapsed_ms: float = (time.perf_counter() - start_time) * 1000.0

        return AgentPayload(
            node_id="07",
            execution_time_ms=round(elapsed_ms, 3),
            tokens_consumed=response.tokens_used or 0,
            data=response.content,
            metadata={
                "status": "success",
                "model": response.model_name,
            },
        )
