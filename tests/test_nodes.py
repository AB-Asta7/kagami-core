import pytest
from src.base import AGENT_REGISTRY, AgentPayload, register_node
from src.dispatcher import Dispatcher
from src.nodes.node_08 import Node08BackendAudit
from src.nodes.node_04 import Node04GachaRisk


@pytest.fixture(autouse=True)
def ensure_nodes_registered():
    """Garantiza que los nodos 08 y 04 estén en AGENT_REGISTRY para cada test."""
    AGENT_REGISTRY["08"] = Node08BackendAudit
    AGENT_REGISTRY["04"] = Node04GachaRisk
    yield


def test_node_08_execution_clean_code():
    dispatcher = Dispatcher()
    clean_code = "def suma(a: int, b: int) -> int:\n    return a + b\n"

    payload = AgentPayload(node_id="test_runner", execution_time_ms=0.0, data=clean_code)
    output = dispatcher.dispatch("08", payload)

    assert output.metadata.get("status") != "error", f"Error en nodo 08: {output.metadata}"
    assert output.node_id == "08"
    assert output.data is not None
    assert output.data["status"] == "APPROVED"
    assert output.data["pep8_long_line_violations"] == 0
    assert output.tokens_consumed > 0


def test_node_04_gacha_probability_calculation():
    dispatcher = Dispatcher()
    # 90 tiros con tasa de 0.6% (0.006)
    data = {"base_rate": 0.006, "pulls": 90}

    payload = AgentPayload(node_id="test_runner", execution_time_ms=0.0, data=data)
    output = dispatcher.dispatch("04", payload)

    assert output.metadata.get("status") != "error", f"Error en nodo 04: {output.metadata}"
    assert output.node_id == "04"
    assert output.data is not None
    assert output.data["node_name"] == "Shisū Sumire"
    # 1 - (0.994)^90 = 0.41818... redondeado a 4 decimales da 0.4182
    assert output.data["cumulative_success_probability"] == pytest.approx(0.4182, abs=1e-4)
