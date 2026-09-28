```markdown
# KAGAMI Core: Deterministic Multi-Agent Orchestration Engine

A lightweight, fault-tolerant multi-agent orchestration framework written in Python. Designed for high-reliability automation, strict separation of concerns, and token-constrained execution environments.

---

## Architecture & Design Patterns

The engine decouples orchestration from execution through four architectural guarantees:

1. **Strict I/O Contracts (Pydantic v2):** Communication occurs via immutable `AgentPayload` schemas capturing latency (`execution_time_ms`), token consumption, and typed output.
2. **Dynamic Inversion of Control:** Decentralized node registration via `@register_node` decorator pattern, preventing circular dependencies and core coupling.
3. **Deterministic Ring Buffering:** `SlidingWindowContext` implemented via `collections.deque` providing FIFO eviction in $O(1)$ time complexity when token budgets are reached.
4. **Resilient Message Broker:** Centralized dispatcher with defensive exception handling, returning structured error payloads to preserve engine uptime during node execution failures.

```mermaid
flowchart TD
    In[Input Task] --> Broker[Message Broker / Dispatcher]
    Broker --> RBAC{Registry & Permissions}
    RBAC -->|Validated| Node[Registered Node Node_ID]
    RBAC -->|Denied / Unknown| Err[Structured Error Payload]
    Node --> Mem[SlidingWindowContext O(1) FIFO]
    Mem --> Out[Immutable AgentPayload]
    Out --> Broker

```

---

## Directory Structure

```text
kagami-core/
├── config/
│   └── agents.yaml
├── src/
│   ├── __init__.py
│   ├── base.py              # AgentPayload contracts and BaseAgent ABC
│   ├── context.py           # SlidingWindowContext (FIFO ring buffer)
│   ├── dispatcher.py        # Resilient message broker and router
│   └── nodes/               # Registered node implementations
│       ├── node_08.py       # Code audit engine (PEP 8, type analysis)
│       └── node_04.py       # Stochastic and discrete probability modeling
├── tests/
│   ├── test_base.py
│   ├── test_context.py
│   ├── test_dispatcher.py
│   └── test_nodes.py
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md

```

---

## Built-in Modules

* **Node 08 (Code Audit):** Static analysis pipeline for PEP 8 compliance, line-length constraints, and type annotation validation.
* **Node 04 (Stochastic Engine):** Cumulative probability modeling using geometric distributions ($1 - (1 - p)^n$) and discrete simulation models.

---

## Verification & Metrics

The test suite covers payload immutability, ID collisions, FIFO buffer eviction, and fault-tolerant routing.

* **Test Framework:** `pytest 9.1`
* **Test Coverage:** 11 unit & integration tests passing (100% pass rate)
* **Execution Latency:** ~0.09s in containerized runtime

```bash
# Run tests locally
pytest -v

```

---

## Containerization & Deployment

Packaged as a rootless, multi-stage OCI-compliant container:

```bash
# Build rootless image using Podman or Docker
podman build -t kagami-core:v1 .

# Execute isolated test suite
podman run --rm localhost/kagami-core:v1

```

* **Base Runner:** `python:3.12-slim` (Debian GNU/Linux 12)
* **Security Profile:** Non-root execution (`appuser`, UID 10001)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
