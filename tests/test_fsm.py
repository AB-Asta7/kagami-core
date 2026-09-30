import pytest
from src.base import AGENT_REGISTRY, AgentPayload
from src.dispatcher import Dispatcher
from src.nodes.node_05_fsm import Node05GachaFSM


@pytest.fixture(autouse=True)
def setup_node_05():
    AGENT_REGISTRY["05"] = Node05GachaFSM
    yield


def test_fsm_hard_pity_determinism():
    dispatcher = Dispatcher()

    # Tasa 0.0 absoluta para forzar el salto exacto a Hard Pity al tiro 90
    data = {
        "base_rate": 0.0,
        "soft_pity_start": 90,
        "hard_pity": 90,
        "pity_increment": 0.0,
        "target_pulls": 90,
        "seed": 42,
    }

    payload = AgentPayload(node_id="test_runner", execution_time_ms=0.0, data=data)
    result = dispatcher.dispatch("05", payload)

    assert result.metadata.get("status") == "success"
    assert result.node_id == "05"
    assert result.data["total_5_stars"] == 1
    assert result.data["items"][0]["pity_count"] == 90


def test_fsm_guaranteed_mechanism():
    dispatcher = Dispatcher()

    # Si entra con garantizado activo, el primer 5 estrellas debe ser promocional
    data = {
        "base_rate": 1.0,  # 100% de éxito inmediato
        "target_pulls": 1,
        "has_guaranteed": True,
        "seed": 10,
    }

    payload = AgentPayload(node_id="test_runner", execution_time_ms=0.0, data=data)
    result = dispatcher.dispatch("05", payload)

    assert result.data["total_5_stars"] == 1
    assert result.data["items"][0]["is_promotional"] is True
    # Tras consumir el garantizado, el siguiente tiro vuelve a ser 50/50 normal
    assert result.data["guaranteed_active_next"] is False
