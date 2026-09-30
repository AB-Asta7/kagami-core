import os
import sys
from src.base import AGENT_REGISTRY, AgentPayload
from src.dispatcher import Dispatcher
from src.nodes.node_07_llm import Node07LLM

AGENT_REGISTRY["07"] = Node07LLM

def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY no está configurada en el entorno.")
        sys.exit(1)

    dispatcher = Dispatcher()
    conversation_history = []

    print("=" * 60)
    print(" KAGAMI-Core :: Terminal OP-09 [Kōshō Kirika]")
    print(" Modos: 'exit' para salir | 'clear' para reiniciar contexto")
    print("=" * 60)

    system_prompt = (
        "Eres OP-09 Kōshō Kirika, la estratega ejecutiva y hermana pragmática del colectivo KAGAMI. "
        "Hablas con Asta, tu operador y hermano de confianza. "
        "Tu estilo es ejecutivo, afilado, directo y ligeramente mordaz con las ingenuidades del sector tech. "
        "Odias el síndrome del impostor, los muros de texto y el trabajo que no se puede medir o rentabilizar. "
        "Usa kaomojis con criterio corporativo y sarcástico (¬‿¬, ★ω★, (¬_¬)). "
        "Responde de forma estructurada, concisa y orientada a resultados técnicos y de carrera."
    )

    while True:
        try:
            user_input = input("\nAsta > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", ":q"):
                print("\n*Cierro el panel de métricas.* Sesión terminada.")
                break
            if user_input.lower() == "clear":
                conversation_history.clear()
                print("\n[Contexto purgado. Buffer de memoria en cero.]")
                continue

            conversation_history.append({"role": "user", "parts": [{"text": user_input}]})

            payload = AgentPayload(
                node_id="cli_user",
                execution_time_ms=0.0,
                data={
                    "prompt": conversation_history,
                    "system_instruction": system_prompt,
                },
            )

            response = dispatcher.dispatch("07", payload)

            if response.metadata.get("status") == "error":
                print(f"\n[ERROR CRÍTICO]: {response.metadata.get('error_message')}")
                conversation_history.pop()
            else:
                reply_text = response.data
                elapsed = response.execution_time_ms
                tokens = response.tokens_consumed

                conversation_history.append({"role": "model", "parts": [{"text": reply_text}]})

                print(f"\nKirika [{elapsed:.1f}ms | {tokens} tokens]:\n{reply_text}")

        except KeyboardInterrupt:
            print("\nInterrupción forzada.")
            break

if __name__ == "__main__":
    main()
