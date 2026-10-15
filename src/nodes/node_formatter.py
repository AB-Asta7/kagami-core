from typing import Any
from src.base import BaseAgent, AgentPayload, register_node


@register_node("formatter")
class GachaReportFormatterNode(BaseAgent):
    """Nodo adaptador: transforma métricas de simulación en prompt analítico riguroso."""
    node_id: str = "formatter"

    def __init__(self, max_context_tokens: int = 1024) -> None:
        super().__init__(max_context_tokens=max_context_tokens)

    def process_task(self, payload: AgentPayload[Any]) -> AgentPayload[Any]:
        sim_data = payload.data if isinstance(payload.data, dict) else {}
        total_pulls = sim_data.get("total_pulls", 0)
        initial_guaranteed = sim_data.get("initial_guaranteed", False)
        soft_pity_start = sim_data.get("soft_pity_start", 74)
        hard_pity = sim_data.get("hard_pity", 90)
        worst_case = sim_data.get("worst_case_promo_pulls", 180)
        pity_state = sim_data.get("current_pity", 0)
        items = sim_data.get("items", [])
        total_5 = sim_data.get("total_5_stars", len(items))
        obtained = sim_data.get("obtained_targets", sim_data.get("promotional_count", 0))
        guaranteed_next = sim_data.get("guaranteed_active_next", False)

        if items:
            pulls_detail = ", ".join(
                [
                    f"Tiro #{i['pull_number']} (Pity {i['pity_count']}, "
                    f"Motivo: {i.get('acquisition_reason', 'PROMO' if i.get('is_promotional') else '50_50_PERDIDO')})"
                    for i in items
                ]
            )
        elif total_5 > 0:
            pulls_detail = f"{total_5} unidad(es) 5★ registrada(s) sin desglose individual en 'items'"
        else:
            pulls_detail = "Ningún 5★ obtenido"

        prompt_text = (
            f"Actúa como OP-09 Kōshō Kirika. Genera un reporte ejecutivo riguroso sobre esta simulación gacha:\n"
            f"- Tiradas ejecutadas: {total_pulls}\n"
            f"- Garantía promocional previa al iniciar: {'Sí' if initial_guaranteed else 'No'}\n"
            f"- Parámetros del banner: Soft Pity={soft_pity_start} | Hard Pity={hard_pity} | Peor escenario promocional={worst_case} tiradas\n"
            f"- Total de 5★ obtenidos: {total_5} ({pulls_detail})\n"
            f"- Unidades promocionales aseguradas: {obtained}\n"
            f"- Pity residual acumulado (heredable): {pity_state}/{hard_pity}\n"
            f"- Garantía (100%) activa para el próximo 5★: {'Sí' if guaranteed_next else 'No'}\n\n"
            f"REGLAS DE AUDITORÍA (PROTOCOLO KAGAMI / RAILYN-002):\n"
            f"1. Distingue explícitamente si cada 5★ promocional provino de 'GARANTIZADO_PREVIO' o de '50_50_GANADO'.\n"
            f"2. No califiques un resultado dentro de la ventana de Soft Pity ({soft_pity_start}-{hard_pity}) como desviación estadísticamente anómala.\n"
            f"3. Valora el Pity residual ({pity_state}) como capital de progreso transferible al siguiente banner, separándolo de la decisión táctica de detener tiradas tras lograr el objetivo.\n"
            f"4. No modifiques ninguna cifra ni infieras estados ocultos."
        )

        return AgentPayload(
            node_id=self.node_id,
            execution_time_ms=1.0,
            tokens_consumed=0,
            data={"prompt": prompt_text, "raw_metrics": sim_data},
            metadata={"status": "success"},
        )
