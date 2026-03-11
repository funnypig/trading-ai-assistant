# Multi-Agent Architecture Diagrams + Implementation Notes (Mermaid, Async In-Process)

**Summary**
Produce a design deliverable that includes:
- A Mermaid **module/flow diagram** matching your sketch (TypeIdent → PromptEnhance → ExecutionBranch → Router → Sub‑Agents → Synthesis → Output).
- A Mermaid **class/interface diagram** specifying core modules, classes, and responsibilities.
- A concrete list of **observability and serving considerations** (OTel + Prometheus, structured logs, tracing, debug tooling).
- A forward‑compatible architecture for **horizontal scaling** and future sub‑agents/tools.

**Important Interfaces and Types**
- `RequestEnvelope`: `{ request_id, user_input, metadata, timestamp }`
- `AgentContext`: `{ request, state, artifacts, trace_ctx }`
- `NodeResult`: `{ status, updates, artifacts, next_hops }`
- `AgentResult`: `{ summary, signals, confidence, artifacts }`
- `ToolResult`: `{ data, errors, latency_ms }`
- `ExecutionPlan`: `{ route, priority, timeouts, policies }`
- `BaseNode.run(ctx) -> NodeResult`
- `BaseAgent.run(ctx) -> AgentResult`
- `BaseTool.run(input) -> ToolResult`

**Design Deliverables**
1. **Mermaid Flow/Module Diagram**  
   - Nodes: `TypeIdentNode`, `PromptEnhanceNode`, `ExecutionBranch`, `RouterNode`, `SentimentAgent`, `TechnicalAgent`, `OptionsAgent`, `FundamentalAgent`, `SynthesisNode`, `Output`.  
   - Include “future / repeated” execution loop branch and “on‑demand sub‑agents” fan‑out.
2. **Mermaid Class Diagram**  
   - Packages: `api`, `graph`, `agents`, `tools`, `domain`, `tasks`, `observability`.  
   - Show inheritance (`BaseNode`, `BaseAgent`, `BaseTool`), composition (`RouterNode` uses `RoutingPolicy`), and external adapters (`LLMClient`, `ToolRegistry`).
3. **Scalability Notes**  
   - Stateless orchestration; all state stored externally (`Redis/DB`) by `request_id`.
   - Idempotent node execution + deterministic retries.
   - Async worker pool with configurable concurrency limits per tool.
4. **Monitoring/Debugging/Logging Notes**  
   - OpenTelemetry tracing, Prometheus metrics, JSON logs with correlation IDs.
   - Sampling strategies, error budgets, per‑agent SLOs.
   - Debug modes: route‑only, tool‑only, replay from stored context.

---

## Implementation Plan

1. **Inspect existing repo structure**
   - Map current folders (`src/app/agents`, `graph`, `tasks`, `observability`, `tools`) to intended modules.
   - Identify existing tool implementations to wrap in `BaseTool` (e.g., `option_max_pain_value.py`).

2. **Define core module layout**
   - `src/app/domain/`: dataclasses for `RequestEnvelope`, `AgentContext`, results.
   - `src/app/graph/`: `BaseNode`, `TypeIdentNode`, `PromptEnhanceNode`, `RouterNode`, `SynthesisNode`, `ExecutionBranch`.
   - `src/app/agents/`: `BaseAgent`, `SentimentAgent`, `TechnicalAgent`, `OptionsAgent`, `FundamentalAgent`.
   - `src/app/tools/`: `BaseTool`, `ToolRegistry`, mocks, adapters to current tools.
   - `src/app/tasks/`: async worker pool, job dispatcher, execution policy.
   - `src/app/observability/`: logger setup, tracer, metrics.

3. **Define decision‑complete behavior**
   - Routing policy defaults: rule‑based first (deterministic), LLM routing as optional strategy.
   - Execution: async in‑process queue with bounded concurrency, timeouts, and retry policy per tool.
   - Synthesis merges signals with confidence + error handling for missing agents.

4. **Produce diagrams**
   - Mermaid flowchart reflecting your sketch and async branch.
   - Mermaid class diagram reflecting modules/classes + relationships.
   - Include a short legend for mock vs real implementations.

5. **Document observability and serving considerations**
   - Standardized log fields (`request_id`, `node`, `agent`, `latency_ms`, `status`).
   - Metrics: request latency, per‑agent latency, tool errors, queue depth.
   - Tracing: spans per node/agent/tool; propagate W3C trace headers.

---

## Test Cases and Scenarios
1. **Routing smoke test**: `TypeIdentNode` → `RouterNode` selects correct agents for a known request.
2. **Agent timeout test**: `OptionsAgent` exceeds timeout → fallback handled by `SynthesisNode`.
3. **Tool mock test**: `ToolRegistry` returns mock tool output deterministically.
4. **Concurrency test**: multiple agents execute in parallel; responses merged deterministically.
5. **Observability test**: logs contain `request_id`, trace spans created for each node.

---

## Assumptions and Defaults
- Diagrams delivered as Mermaid in response (no repo file changes unless requested).
- Async in‑process execution is the default; Celery/Hyrbid is a future option.
- OpenTelemetry + Prometheus is the observability baseline.
- Language model provider is abstracted via `LLMClient` interface (pluggable).

