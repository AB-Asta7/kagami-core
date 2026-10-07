from typing import Any
from src.base import BaseAgent, AgentPayload


class GachaReportFormatterNode(BaseAgent):
    """Nodo adaptador: transforma métricas de simulación en prompt analítico."""
    node_id: str = "formatter"

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
