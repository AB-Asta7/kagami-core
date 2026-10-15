import importlib
import os
import pkgutil
import sys
import yaml
from pathlib import Path
from typing import Dict, Any
from src.base import AgentPayload
from src.context import SlidingWindowContext
from src.dispatcher import Dispatcher
from src.kernel.kaname import ChusuKanameKernel
import src.nodes
from src.nodes.node_formatter import GachaReportFormatterNode
from dotenv import load_dotenv
load_dotenv()

# Auto-registro dinámico de todos los nodos en src/nodes/
for _, module_name, _ in pkgutil.iter_modules(src.nodes.__path__):
    importlib.import_module(f"src.nodes.{module_name}")


def load_operators_manifest(path: str = "config/agents.yaml") -> Dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"No se encontró el manifiesto canónico en {path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("operators", {})


def parse_simulate_command(cmd_str: str) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "target_pulls": 90,
        "base_rate": 0.006,
        "soft_pity_start": 74,
        "hard_pity": 90,
        "has_guaranteed": False,
    }
    parts = cmd_str.strip().split()[1:]
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip().lower()
            v = v.strip().lower()
            if k in ("pulls", "target_pulls"):
                params["target_pulls"] = int(v)
            elif k in ("guaranteed", "has_guaranteed"):
                params["has_guaranteed"] = v in ("true", "1", "yes", "si", "sí")
            elif k == "seed":
                params["seed"] = int(v)
    return params


def extract_response_text(data: Any) -> str:
    """Extrae el texto de respuesta sin importar si el nodo devuelve dict o str."""
    if isinstance(data, dict):
        return str(data.get("response", data.get("prompt", str(data))))
    return str(data)


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        print("[ERROR CRÍTICO]: GEMINI_API_KEY no detectada en el entorno.")
        sys.exit(1)

    operators = load_operators_manifest()
    active_op_id = "OP-09"
    contexts: Dict[str, SlidingWindowContext] = {
        op_id: SlidingWindowContext(max_tokens=cfg.get("max_context_tokens", 2048))
        for op_id, cfg in operators.items()
    }

    dispatcher = Dispatcher()

    kernel = ChusuKanameKernel(
        dispatcher=dispatcher,
        telemetry_path="logs/telemetry.jsonl",
    )

    print("=" * 68)
    print("  KAGAMI-CORE // CONSOLA MULTI-OPERADORA (CANONICAL REGISTRY V2)")
    print("  Comandos: /ops | /switch OP-XX | /simulate pulls=90 | /clear | /exit")
    print("=" * 68)

    while True:
        try:
            active_cfg = operators[active_op_id]
            prompt_label = f"\n[{active_op_id} {active_cfg['name']}] <Asta>: "
            user_input = input(prompt_label).strip()
            if not user_input:
                continue

            cmd_lower = user_input.lower()
            if cmd_lower in ("/exit", "exit", "quit"):
                print(f"\n[{active_op_id}]: Cerrando sesión de terminal. Hasta pronto, Asta.")
                break

            if cmd_lower == "/ops":
                print("\n--- MATRIZ FUNCIONAL GLOBAL: PROTOCOLO KAGAMI ---")
                for op_id, cfg in operators.items():
                    marker = "▶" if op_id == active_op_id else " "
                    ctx_tokens = contexts[op_id].current_tokens
                    max_t = contexts[op_id].max_tokens
                    print(f" {marker} [{op_id}] {cfg['name']:<18} | {cfg['domain']:<26} | Buffer: {ctx_tokens}/{max_t} tok")
                continue

            if cmd_lower.startswith("/switch"):
                parts = user_input.split()
                if len(parts) < 2:
                    print("Uso: /switch OP-XX (Ejemplo: /switch OP-01 o /switch OP-04)")
                    continue
                target_op = parts[1].upper()
                if target_op in operators:
                    active_op_id = target_op
                    new_cfg = operators[active_op_id]
                    print(f"\n🔄 [KERNEL KANAME]: Enrutamiento conmutado a [{active_op_id}] {new_cfg['name']} ({new_cfg['domain']}).")
                else:
                    print(f"❌ Operadora '{target_op}' no existe en el registro canónico (OP-00 a OP-11).")
                continue

            if cmd_lower == "/clear":
                contexts[active_op_id].clear()
                print(f"🧹 [BUFFER FIFO]: Memoria de [{active_op_id}] {active_cfg['name']} purgada a 0 tokens.")
                continue

            if cmd_lower.startswith("/simulate"):
                sim_params = parse_simulate_command(user_input)
                print(f"\n⚙️ [KERNEL KANAME]: Ejecutando Pipeline Determinista ['05' -> 'formatter' -> '07']...")
                init_payload = AgentPayload(node_id="user", execution_time_ms=0.0, tokens_consumed=0, data=sim_params)
                result = kernel.execute_pipeline(["05", "formatter", "07"], init_payload)
                response_text = extract_response_text(result.data)
                total_t = result.metadata.get("total_pipeline_time_ms", 0.0)
                total_tok = result.metadata.get("total_tokens_consumed", 0)
                print(f"\n[OP-09 Kōshō Kirika // Reporte FSM]:\n{response_text}")
                print(f"\n📊 [TELEMETRÍA KERNEL]: Tiempo Total: {total_t} ms | Tokens: {total_tok}")
                continue

            # Flujo conversacional con memoria FIFO (SlidingWindowContext)
            op_context = contexts[active_op_id]
            user_tokens = max(1, len(user_input.split()) * 2)
            op_context.add_message("Asta", user_input, token_cost=user_tokens)

            history_block = "\n".join(
                [f"{m['role']}: {m['content']}" for m in op_context.get_messages()]
            )
            full_prompt = (
                f"[SISTEMA - IDENTIDAD ACTIVA]:\n{active_cfg['system_prompt']}\n\n"
                f"[HISTORIAL RECIENTE (COLA FIFO)]:\n{history_block}\n\n"
                f"Responde como {active_op_id} ({active_cfg['name']}) directamente a Asta:"
            )

            llm_payload = AgentPayload(
                node_id="user",
                execution_time_ms=0.0,
                tokens_consumed=0,
                data={"prompt": full_prompt},
            )
            result = kernel.execute_pipeline(["07"], llm_payload)
            reply = extract_response_text(result.data)
            reply_tokens = max(1, len(reply.split()) * 2)
            op_context.add_message(active_cfg["name"], reply, token_cost=reply_tokens)

            total_t = result.metadata.get("total_pipeline_time_ms", 0.0)
            total_tok = result.metadata.get("total_tokens_consumed", 0)
            print(f"\n[{active_op_id} {active_cfg['name']}]:\n{reply}")
            print(f"\n📊 [TELEMETRÍA]: {total_t} ms | Tokens turno: {total_tok} | Buffer FIFO: {op_context.current_tokens}/{op_context.max_tokens}")

        except KeyboardInterrupt:
            print("\nSesión finalizada por interrupción de teclado.")
            break
        except Exception as e:
            print(f"\n[EXCEPCIÓN DE SISTEMA]: {e}")


if __name__ == "__main__":
    main()
