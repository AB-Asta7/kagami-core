from unittest.mock import MagicMock
import pytest
from src.base import AGENT_REGISTRY, AgentPayload
from src.dispatcher import Dispatcher
from src.nodes.node_07_llm import Node07LLM
from src.nodes.node_08 import Node08BackendAudit
from src.clients.gemini_client import LLMResponse


@pytest.fixture(autouse=True)
def setup_pipeline_nodes():
    """Registra los nodos necesarios para el pipeline."""
    AGENT_REGISTRY["07"] = Node07LLM
    AGENT_REGISTRY["08"] = Node08BackendAudit
    yield


def test_e2e_llm_generation_to_backend_audit_pipeline():
    dispatcher = Dispatcher()

    # 1. Simular la respuesta del LLM con código Python válido y limpio
    generated_python_code = (
        "def calcular_tasa_exito(tiros: int) -> float:\n"
        "    probabilidad_base = 0.006\n"
        "    return 1.0 - ((1.0 - probabilidad_base) ** tiros)\n"
    )

    mock_adapter = MagicMock()
    mock_adapter.generate.return_value = LLMResponse(
        content=generated_python_code,
        model_name="gemini-2.5-flash",
        tokens_used=48,
    )

    # Inyectar el adaptador mockeado en la instancia del nodo 07 administrada por el dispatcher
    agent_07 = dispatcher.get_or_create_agent("07")
    agent_07.adapter = mock_adapter

    # 2. Paso 1: Ejecutar inferencia en Nodo 07
    input_payload = AgentPayload(
        node_id="client_request",
        execution_time_ms=0.0,
        data={
            "prompt": "Escribe una función pura para calcular probabilidad acumulada.",
            "system_instruction": "Genera solo código Python limpio cumpliendo PEP8.",
        },
    )

    llm_output = dispatcher.dispatch("07", input_payload)

    assert llm_output.metadata.get("status") == "success"
    assert llm_output.tokens_consumed == 48
    assert llm_output.data == generated_python_code

    # 3. Paso 2: Encadenar la salida del LLM directamente al Nodo 08 (Backend Audit)
    audit_payload = AgentPayload(
        node_id="07",
        execution_time_ms=0.0,
        data=llm_output.data,
    )

    audit_output = dispatcher.dispatch("08", audit_payload)

    # 4. Validar el veredicto del Nodo 08 sobre el código generado por la IA
    assert audit_output.metadata.get("status") != "error"
    assert audit_output.node_id == "08"
    assert audit_output.data["status"] == "APPROVED"
    assert audit_output.data["pep8_long_line_violations"] == 0
    assert audit_output.tokens_consumed > 0
