import time
from typing import Any
import pytest
from pydantic import ValidationError

from src.base import (
    AGENT_REGISTRY,
    AgentPayload,
    BaseAgent,
    get_agent_instance,
    register_node,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Aisla el registro de nodos entre tests."""
    AGENT_REGISTRY.clear()
    yield
    AGENT_REGISTRY.clear()


def test_agent_payload_immutability():
    payload = AgentPayload(
        node_id="08",
        execution_time_ms=12.5,
        tokens_consumed=150,
        data={"status": "optimal"}
    )
    with pytest.raises(ValidationError):
        payload.tokens_consumed = 200  # type: ignore


def test_node_registration_and_execution():
    @register_node("08")
    class MockBackendAgent(BaseAgent):
        def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
            start = time.perf_counter()
            processed_data = f"Processed: {payload.data}"
            return self.emit_success(data=processed_data, start_time=start, tokens=10)

    assert "08" in AGENT_REGISTRY
    agent = get_agent_instance("08", max_context_tokens=2048)
    assert agent.node_id == "08"
    assert agent.max_context_tokens == 2048

    input_payload = AgentPayload(
        node_id="00",
        execution_time_ms=0.0,
        data="raw_query"
    )
    output_payload = agent.process_task(input_payload)

    assert output_payload.node_id == "08"
    assert output_payload.data == "Processed: raw_query"
    assert output_payload.tokens_consumed == 10
    assert output_payload.execution_time_ms >= 0.0


def test_collision_registration_fails():
    @register_node("01")
    class FirstAgent(BaseAgent):
        def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
            return payload

    with pytest.raises(KeyError):
        @register_node("01")
        class DuplicateAgent(BaseAgent):
            def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
                return payload
