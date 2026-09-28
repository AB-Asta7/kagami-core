from __future__ import annotations

import json
from typing import Any
from src.base import AgentPayload
from src.dispatcher import Dispatcher

# Importación obligatoria para ejecutar los decoradores @register_node
import src.nodes.node_08
import src.nodes.node_04


def print_separator(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"// {title}")
    print("=" * 60)


def print_payload(payload: AgentPayload[Any]) -> None:
    print(f"[*] Emisor / Nodo : {payload.node_id}")
    print(f"[*] Latencia      : {payload.execution_time_ms:.3f} ms")
    print(f"[*] Tokens Cost   : {payload.tokens_consumed}")
    print(f"[*] Payload Data  :")
    print(json.dumps(payload.data, indent=4, ensure_ascii=False))
    if payload.metadata:
        print(f"[*] Metadatos     : {payload.metadata}")


def main() -> None:
    print_separator("INICIALIZANDO MOTOR KAGAMI-CORE // SESIÓN INTERACTIVA")
    dispatcher = Dispatcher(default_max_tokens=4096)
    print("[+] Despachador instanciado y listo.")

    # --------------------------------------------------------------------------
    # Tarea 1: Auditoría de código con Nodo 08 (Kōdo Senna)
    # --------------------------------------------------------------------------
    print_separator("EJECUCIÓN NODO 08: AUDITORÍA ESTÁTICA PEP 8")

    codigo_prueba = (
        "def calcular_ratio(exitos: int, total: int) -> float:\n"
        "    if total == 0:\n"
        "        return 0.0\n"
        "    return round(exitos / total, 4)\n"
    )

    payload_in_08 = AgentPayload(
        node_id="gateway_cli",
        execution_time_ms=0.0,
        data=codigo_prueba,
    )

    print("[-] Transfiriendo payload tipado hacia Nodo 08...")
    resultado_08 = dispatcher.dispatch(
        target_node_id="08",
        payload=payload_in_08,
    )
    print_payload(resultado_08)

    # --------------------------------------------------------------------------
    # Tarea 2: Cálculo estocástico de gacha con Nodo 04 (Shisū Sumire)
    # --------------------------------------------------------------------------
    print_separator("EJECUCIÓN NODO 04: MODELADO DE PROBABILIDAD ESTOCÁSTICA")

    datos_gacha = {
        "base_rate": 0.006,  # 0.6% base
        "pulls": 90,         # 90 tiros acumulados
    }

    payload_in_04 = AgentPayload(
        node_id="gateway_cli",
        execution_time_ms=0.0,
        data=datos_gacha,
    )

    print("[-] Transfiriendo parámetros de simulación hacia Nodo 04...")
    resultado_04 = dispatcher.dispatch(
        target_node_id="04",
        payload=payload_in_04,
    )
    print_payload(resultado_04)

    # --------------------------------------------------------------------------
    # Tarea 3: Verificación de Tolerancia a Fallos (Nodo inexistente)
    # --------------------------------------------------------------------------
    print_separator("PRUEBA DE TOLERANCIA A FALLOS (DEFENSIVE DISPATCH)")

    payload_in_fail = AgentPayload(
        node_id="gateway_cli",
        execution_time_ms=0.0,
        data={"action": "unregistered_test"},
    )

    print("[-] Intentando enrutar hacia nodo no registrado ('99')...")
    resultado_fail = dispatcher.dispatch(
        target_node_id="99",
        payload=payload_in_fail,
    )
    print_payload(resultado_fail)


if __name__ == "__main__":
    main()
