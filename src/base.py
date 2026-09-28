from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, Generic, Optional, Type, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class AgentPayload(BaseModel, Generic[T]):
    """
    Esquema inmutable para la transferencia de datos y telemetría inter-nodo.
    """
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    node_id: str = Field(..., description="Identificador único del nodo (e.g. '08', '09')")
    execution_time_ms: float = Field(..., ge=0.0, description="Latencia de procesamiento en milisegundos")
    tokens_consumed: int = Field(default=0, ge=0, description="Volumen de tokens o costo computacional")
    timestamp: float = Field(default_factory=time.time, description="Epoch UNIX de la emisión")
    data: T = Field(..., description="Carga útil validada emitida por el agente")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos auxiliares de ruteo")


class BaseAgent(ABC):
    """
    Clase abstracta base para todos los agentes del protocolo KAGAMI.
    """
    node_id: ClassVar[str]
    max_context_tokens: int

    def __init__(self, max_context_tokens: int = 4096) -> None:
        if not hasattr(self.__class__, "node_id") or not self.__class__.node_id:
            raise ValueError(f"La clase {self.__class__.__name__} debe declarar un 'node_id' estático.")
        self.max_context_tokens = max_context_tokens

    @abstractmethod
    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        """
        Punto de entrada de ejecución del nodo. Debe ser idempotente y determinista.
        """
        pass

    def emit_success(
        self,
        data: Any,
        start_time: float,
        tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentPayload[Any]:
        """
        Construye el payload de salida con cálculo de latencia de ejecución.
        """
        elapsed_ms: float = (time.perf_counter() - start_time) * 1000.0
        return AgentPayload(
            node_id=self.node_id,
            execution_time_ms=round(elapsed_ms, 3),
            tokens_consumed=tokens,
            data=data,
            metadata=metadata or {}
        )


AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {}


def register_node(node_id: str) -> Callable[[Type[BaseAgent]], Type[BaseAgent]]:
    """
    Decorador para registrar nodos de forma desacoplada en el bus central.
    """
    def decorator(cls: Type[BaseAgent]) -> Type[BaseAgent]:
        if not issubclass(cls, BaseAgent):
            raise TypeError(f"El nodo {cls.__name__} debe heredar de BaseAgent.")
        if node_id in AGENT_REGISTRY:
            raise KeyError(f"Colisión de nodos: El identificador '{node_id}' ya está registrado.")
        cls.node_id = node_id
        AGENT_REGISTRY[node_id] = cls
        return cls
    return decorator


def get_agent_instance(node_id: str, **kwargs: Any) -> BaseAgent:
    """
    Factory method para instanciar agentes registrados por ID.
    """
    agent_cls = AGENT_REGISTRY.get(node_id)
    if not agent_cls:
        raise KeyError(f"Nodo '{node_id}' no encontrado en AGENT_REGISTRY.")
    return agent_cls(**kwargs)