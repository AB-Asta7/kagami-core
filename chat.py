import os
import sys
import re
from typing import Dict, Any
from src.base import AGENT_REGISTRY, AgentPayload
from src.dispatcher import Dispatcher
from src.kernel.kaname import ChusuKanameKernel
from src.nodes.node_05_fsm import Node05GachaFSM
from src.nodes.node_07_llm import Node07LLM
from src.nodes.node_formatter import GachaReportFormatterNode

# Registro de operadoras y adaptadores en el bus
AGENT_REGISTRY["05"] = Node05GachaFSM
AGENT_REGISTRY["formatter"] = GachaReportFormatterNode
AGENT_REGISTRY["07"] = Node07LLM


def parse_simulate_command(user_input: str) -> Dict[str, Any]:
    """Extrae parámetros del comando /simulate pulls=X rate=Y."""
    pulls_match = re.search(r"pulls=(\d+)", user_input)
    rate_match = re.search(r"rate=([\d.]+)", user_input)

    target_pulls = int(pulls_match.group(1)) if pulls_match else 90
    base_rate = float(rate_match.group(1)) if rate_match else 0.006

    return {
        "base_rate": base_rate,
        "soft_pity_start": 74,
        "hard_pity": 90,
        "pity_increment": 0.06,
        "target_pulls": target_pulls,
        "has_guaranteed": False,
        "seed": None,
    }


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY no está configurada en el entorno.")
        sys.exit(1)

    dispatcher = Dispatcher()
    kernel = ChusuKanameKernel(
        dispatcher=dispatcher,
        telemetry_path="logs/telemetry.jsonl"
    )

    print("=" * 65)
    print(" KAGAMI-Core :: Terminal OP-09 [Kōshō Kirika] + Chūsu Kaname")
    print(" Comandos: '/simulate pulls=90' | '/clear' | 'exit'")
    print("=" * 65)

    system_prompt = (
        "Eres OP-09 Kōshō Kirika, la estratega ejecutiva y hermana pragmática "
        "del colectivo KAGAMI. Hablas con Asta, tu operador y hermano de confianza. "
        "Tu estilo es ejecutivo, afilado, directo y sin rodeos corporativos vacíos."
    )

    while True:
        try:
            user_input = input("\nAsta > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("\nKirika > Sesión cerrada. Cero deuda técnica.")
                break

            if user_input.startswith("/simulate"):
                print("\n[Kaname :: Supervisor] Iniciando pipeline E2E...")
                sim_params = parse_simulate_command(user_input)
                
                payload = AgentPayload(
                    node_id="cli_operator",
                    execution_time_ms=0.0,
                    data=sim_params,
                )

                # Despacho atómico supervisado
                final_payload = kernel.execute_pipeline(["05", "formatter", "07"], payload)

                print(f"\nKirika > {final_payload.data}\n")
                meta = final_payload.metadata
                print(f"[Telemetría] Tiempo: {meta.get('total_pipeline_time_ms')} ms | "
                      f"Tokens: {meta.get('total_tokens_consumed')} | Log: logs/telemetry.jsonl")
                continue

            # Modo conversacional estándar directo con Kirika
            prompt = f"{system_prompt}\n\nAsta: {user_input}\nKirika:"
            payload = AgentPayload(
                node_id="cli_user",
                execution_time_ms=0.0,
                data={"prompt": prompt},
            )
            result = dispatcher.dispatch("07", payload)
            print(f"\nKirika > {result.data}")

        except KeyboardInterrupt:
            print("\nKirika > Interrupción forzada.")
            break
        except Exception as e:
            print(f"\n[Error de Ejecución] {e}")


if __name__ == "__main__":
    main()
