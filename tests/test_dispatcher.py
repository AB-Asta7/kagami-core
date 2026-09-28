import time
from typing import Any
import pytest
from src.base import AGENT_REGISTRY, AgentPayload, BaseAgent, register_node
from src.dispatcher import Dispatcher


@pytest.fixture(autouse=True)
def clean_registry():
    """Limpia el registro de nodos antes y después de cada test."""
    AGENT_REGISTRY.clear()
    yield
    AGENT_REGISTRY.clear()


def test_dispatcher_successful_routing():
    @register_node("08")
    class MockBackendAgent(BaseAgent):
        def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
            start = time.perf_counter()
            return self.emit_success(data={"result": payload.data * 2}, start_time=start, tokens=5)

    dispatcher = Dispatcher(default_max_tokens=1024)
    input_payload = AgentPayload(
        node_id="gateway",
        execution_time_ms=0.0,
        data=21,
    )

    output = dispatcher.dispatch("08", input_payload)

    assert output.node_id == "08"
    assert output.data == {"result": 42}
    assert output.tokens_consumed == 5
    assert output.metadata.get("status") != "error"

    # Validar que el contexto del nodo existe y está aislado
    context = dispatcher.get_context("08")
    assert context is not None
    assert context.max_tokens == 1024


def test_dispatcher_fault_tolerance_on_exception():
    @register_node("00")
    class FaultyChaosAgent(BaseAgent):
        def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
            raise ZeroDivisionError("Simulated chaos failure in execution")

    dispatcher = Dispatcher()
    input_payload = AgentPayload(
        node_id="gateway",
        execution_time_ms=0.0,
        data="trigger_crash",
    )

    # El despachador debe atrapar la excepción y no reventar
    output = dispatcher.dispatch("00", input_payload)

    assert output.node_id == "00"
    assert output.data is None
    assert output.metadata["status"] == "error"
    assert output.metadata["exception_type"] == "ZeroDivisionError"
    assert "Simulated chaos failure" in output.metadata["error_message"]


def test_dispatcher_routing_to_unregistered_node():
    dispatcher = Dispatcher()
    input_payload = AgentPayload(
        node_id="gateway",
        execution_time_ms=0.0,
        data="ping",
    )

    output = dispatcher.dispatch("99", input_payload)

    assert output.node_id == "99"
    assert output.metadata["status"] == "error"
    assert output.metadata["exception_type"] == "KeyError"
