import pytest
from typing import Any
from src.base import AGENT_REGISTRY, AgentPayload, BaseAgent
from src.dispatcher import Dispatcher
from src.kernel.kaname import ChusuKanameKernel, KernelExecutionError


class DummyEchoAgent(BaseAgent):
    node_id: str = "dummy_step"

    def __init__(self, max_context_tokens: int = 1024) -> None:
        super().__init__(max_context_tokens=max_context_tokens)

    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        current_val = payload.data.get("val", 0) if isinstance(payload.data, dict) else 0
        return AgentPayload(
            node_id=self.node_id,
            execution_time_ms=5.0,
            tokens_consumed=10,
            data={"val": current_val + 1},
            metadata={"status": "success"},
        )


@pytest.fixture(autouse=True)
def setup_kernel_nodes():
    AGENT_REGISTRY["dummy_step"] = DummyEchoAgent
    yield
    AGENT_REGISTRY.pop("dummy_step", None)


def test_kernel_pipeline_successful_execution():
    dispatcher = Dispatcher()
    kernel = ChusuKanameKernel(dispatcher=dispatcher)

    initial_payload = AgentPayload(
        node_id="test_runner",
        execution_time_ms=0.0,
        data={"val": 10},
    )

    result = kernel.execute_pipeline(["dummy_step", "dummy_step"], initial_payload)

    assert result.data["val"] == 12
    assert result.metadata["kernel_supervisor"] == "Chūsu Kaname"
    assert result.metadata["pipeline_length"] == 2
    assert result.metadata["total_tokens_consumed"] == 20
    assert len(kernel.execution_audit_log) == 2


def test_kernel_token_quota_enforcement():
    dispatcher = Dispatcher()
    kernel = ChusuKanameKernel(dispatcher=dispatcher, max_total_tokens=15)

    initial_payload = AgentPayload(
        node_id="test_runner",
        execution_time_ms=0.0,
        data={"val": 0},
    )

    with pytest.raises(KernelExecutionError, match="Presupuesto de tokens excedido"):
        kernel.execute_pipeline(["dummy_step", "dummy_step"], initial_payload)
