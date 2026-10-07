from typing import Any
import pytest
from src.base import AGENT_REGISTRY, AgentPayload, BaseAgent
from src.dispatcher import Dispatcher
from src.kernel.kaname import ChusuKanameKernel
from src.nodes.node_05_fsm import Node05GachaFSM
from src.nodes.node_07_llm import Node07LLM


class GachaReportFormatterNode(BaseAgent):
    """Nodo adaptador que transforma los datos crudos de la FSM en un prompt para el LLM."""
    node_id: str = "fsm_formatter"

    def __init__(self, max_context_tokens: int = 1024) -> None:
        super().__init__(max_context_tokens=max_context_tokens)

    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        sim_data = payload.data if isinstance(payload.data, dict) else {}
        total_pulls = sim_data.get("total_pulls", 0)
        pity_state = sim_data.get("current_pity", 0)
        obtained = sim_data.get("obtained_targets", 0)

        prompt_text = (
            f"Actúa como Kirika. Genera un reporte ejecutivo breve sobre la simulación gacha:\n"
            f"- Total de tiradas realizadas: {total_pulls}\n"
            f"- Pity final acumulado: {pity_state}\n"
            f"- Objetivos obtenidos: {obtained}\n"
            f"Evalúa la eficiencia de recursos y el retorno de inversión."
        )

        return AgentPayload(
            node_id=self.node_id,
            execution_time_ms=1.0,
            tokens_consumed=0,
            data={"prompt": prompt_text, "raw_metrics": sim_data},
            metadata={"status": "success"},
        )


@pytest.fixture(autouse=True)
def setup_e2e_registry():
    AGENT_REGISTRY["05"] = Node05GachaFSM
    AGENT_REGISTRY["formatter"] = GachaReportFormatterNode
    AGENT_REGISTRY["07"] = Node07LLM
    yield
    AGENT_REGISTRY.pop("05", None)
    AGENT_REGISTRY.pop("formatter", None)
    AGENT_REGISTRY.pop("07", None)


def test_kernel_e2e_fsm_to_llm_report():
    dispatcher = Dispatcher()
    kernel = ChusuKanameKernel(
        dispatcher=dispatcher,
        max_total_tokens=4096,
        max_total_time_ms=120000.0,
    )

    simulation_data = {
        "base_rate": 0.006,
        "soft_pity_start": 74,
        "hard_pity": 90,
        "pity_increment": 0.06,
        "target_pulls": 90,
        "has_guaranteed": False,
        "seed": 1337,
    }

    initial_payload = AgentPayload(
        node_id="test_runner",
        execution_time_ms=0.0,
        data=simulation_data,
    )

    # Pipeline supervisado por Kaname: FSM -> Formateador -> LLM
    final_payload = kernel.execute_pipeline(["05", "formatter", "07"], initial_payload)

    assert final_payload.metadata.get("status") == "success"
    assert final_payload.metadata.get("kernel_supervisor") == "Chūsu Kaname"
    assert final_payload.metadata.get("pipeline_length") == 3
    assert len(kernel.execution_audit_log) == 3
    assert isinstance(final_payload.data, str)
    assert len(final_payload.data) > 0
