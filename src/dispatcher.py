from __future__ import annotations

import time
from typing import Any, Dict, Optional
from src.base import AgentPayload, BaseAgent, get_agent_instance
from src.context import SlidingWindowContext


class Dispatcher:
    """
    Orquestador central del protocolo KAGAMI.
    Administra el ciclo de vida de los agentes, sus buffers de memoria y el ruteo de payloads.
    """

    def __init__(self, default_max_tokens: int = 4096) -> None:
        self.default_max_tokens: int = default_max_tokens
        self._active_agents: Dict[str, BaseAgent] = {}
        self._agent_contexts: Dict[str, SlidingWindowContext] = {}

    def get_or_create_agent(self, node_id: str) -> BaseAgent:
        """Obtiene una instancia activa del agente o la inicializa si no existe."""
        if node_id not in self._active_agents:
            agent = get_agent_instance(node_id, max_context_tokens=self.default_max_tokens)
            self._active_agents[node_id] = agent
            self._agent_contexts[node_id] = SlidingWindowContext(max_tokens=self.default_max_tokens)
        return self._active_agents[node_id]

    def get_context(self, node_id: str) -> Optional[SlidingWindowContext]:
        """Devuelve el buffer de memoria aislado del nodo solicitado."""
        return self._agent_contexts.get(node_id)

    def dispatch(self, target_node_id: str, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        """
        Enruta un payload al nodo objetivo garantizando manejo de errores determinista.
        """
        start_time: float = time.perf_counter()
        try:
            agent: BaseAgent = self.get_or_create_agent(target_node_id)
            return agent.process_task(payload)
        except Exception as exc:
            elapsed_ms: float = (time.perf_counter() - start_time) * 1000.0
            return AgentPayload(
                node_id=target_node_id,
                execution_time_ms=round(elapsed_ms, 3),
                tokens_consumed=0,
                data=None,
                metadata={
                    "status": "error",
                    "exception_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
