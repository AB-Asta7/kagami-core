from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextMessage(BaseModel):
    """Representa una unidad atómica dentro del buffer de memoria."""
    role: str = Field(..., description="Rol del emisor (e.g. 'system', 'user', 'assistant')")
    content: str = Field(..., description="Cuerpo del mensaje")
    token_cost: int = Field(default=0, ge=0, description="Peso computacional en tokens")


class SlidingWindowContext:
    """
    Buffer circular de contexto acotado por un límite duro de tokens.
    Implementa poda determinista FIFO en O(1) usando collections.deque.
    """
    def __init__(self, max_tokens: int = 4096) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens debe ser un entero estrictamente positivo.")
        self.max_tokens: int = max_tokens
        self._buffer: Deque[ContextMessage] = deque()
        self._current_tokens: int = 0

    @property
    def current_tokens(self) -> int:
        return self._current_tokens

    def __len__(self) -> int:
        return len(self._buffer)

    def add_message(self, role: str, content: str, token_cost: int) -> None:
        """
        Agrega un mensaje y expulsa los registros antiguos si excede la capacidad.
        """
        if token_cost > self.max_tokens:
            raise ValueError(f"El costo ({token_cost}) excede la capacidad total ({self.max_tokens}).")

        # Poda FIFO determinista mientras el nuevo mensaje desborde el buffer
        while self._current_tokens + token_cost > self.max_tokens and self._buffer:
            evicted: ContextMessage = self._buffer.popleft()
            self._current_tokens -= evicted.token_cost

        msg = ContextMessage(role=role, content=content, token_cost=token_cost)
        self._buffer.append(msg)
        self._current_tokens += token_cost

    def get_messages(self) -> List[Dict[str, Any]]:
        """Exporta el historial en formato lista de diccionarios."""
        return [msg.model_dump() for msg in self._buffer]

    def clear(self) -> None:
        """Purga absoluta de memoria."""
        self._buffer.clear()
        self._current_tokens = 0
