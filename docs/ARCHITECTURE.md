# Architecture — Trading AI Assistant

## Overview

A multi-agent LLM system for financial analysis. The user asks a natural-language question about a stock; the system classifies the task, fans out to up to three specialist AI agents in parallel (fundamental, sentiment, options), and synthesizes their outputs into a coherent answer.

---

## Layer Map

```
┌─────────────────────────────────────────────────────────┐
│  Entry Points                                           │
│  ui/chainlit_app.py  ui/openwebui_pipeline.py  cli/     │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Graph  (graph/graph.py, graph/state.py)                │
│  LangGraph StateGraph — routes, fans out, fans in       │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Agents  (agents/)                                      │
│  nodes/  — graph node wrappers for each agent           │
│  *_agent.py — LangChain agents with bound tools         │
│  tools/  — LangChain @tool wrappers (thin facades)      │
└───────────────────────────┬─────────────────────────────┘
                            │ (only via services/)
┌───────────────────────────▼─────────────────────────────┐
│  Services  (services/)                                  │
│  Business logic: composes data + analysis calculations  │
└──────────────┬────────────────────────┬─────────────────┘
               │                        │
┌──────────────▼──────────┐  ┌──────────▼──────────────────┐
│  Data  (data/finviz/)   │  │  Analysis  (analysis/)       │
│  Finviz Elite HTTP API  │  │  Pure calculation functions  │
│  + Redis cache          │  │  (options math, news util)   │
└──────────────┬──────────┘  └─────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│  Infrastructure  (infrastructure/)                      │
│  cache/ — Redis client + @redis_cache decorator         │
│  persistence/ — PostgreSQL checkpointer factory         │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│  Foundation (no internal imports)                       │
│  domain/models.py   — value objects (News, StockInfo)   │
│  domain/schemas.py  — domain models (Classification)    │
│  domain/ports.py    — provider Protocols                │
│  config/settings.py — env/secrets (BaseSettings)        │
│  config/models.py   — LLM name constants                │
└─────────────────────────────────────────────────────────┘
```

**Dependency rule:** arrows point inward only. `agents/` never imports `data/` directly; it always goes through `services/`.

---

## Module Reference

### `domain/`

| File | Contents |
|------|----------|
| `models.py` | `News`, `StockDescriptiveInfo` — provider-agnostic value objects shared by all layers |
| `schemas.py` | `TaskClassificationResult` — Pydantic model returned by the classifier LLM |
| `ports.py` | `FundamentalDataProvider`, `OptionsDataProvider`, `NewsDataProvider` — `Protocol` interfaces; new data providers implement these |

### `config/`

| File | Contents |
|------|----------|
| `settings.py` | `Settings(BaseSettings)` — reads `.env`; holds API keys, URLs. Instantiates `settings` singleton |
| `models.py` | `SMART_MODEL`, `DATA_ANALYSIS_MODEL`, `MINI_MODEL` — LLM identifier strings; safe to import without `.env` |
| `config.py` | Backward-compat shim re-exporting both modules |

### `graph/`

| File | Contents |
|------|----------|
| `state.py` | `AgentState` — the LangGraph `TypedDict` that flows through every node; `AgentOutput` — per-agent result dict; `_results_reducer` — fan-in reducer |
| `graph.py` | `build_graph()` — pure graph topology (testable without DB); `create_graph()` — production entry point that wires the PostgreSQL checkpointer |

### `agents/`

#### `nodes/`

Each node is a callable class. It pulls the relevant sub-query from `AgentState`, invokes the agent, and writes `AgentOutput` back to state.

| Class | File | Role |
|-------|------|------|
| `TaskClassificationNode` | `task_classification_node.py` | Classifies user query → `TaskClassificationResult`. Uses `MINI_MODEL`. Controls which agents run and passes per-agent refined queries |
| `FundamentalAnalysisNode` | `fundamental_analysis_node.py` | Invokes `fundamental_analysis_agent` |
| `SentimentAnalysisNode` | `sentiment_analysis_node.py` | Initialises the article registry, invokes `sentiment_analysis_agent` |
| `OptionAnalysisNode` | `option_analysis_node.py` | Invokes `options_analysis_agent` |
| `SynthesizeNode` | `synthesize_node.py` | Combines all `AgentOutput` results + stock descriptive context; streams the final answer using `SMART_MODEL` |
| `RecurringTaskNode` | `recurring_task_node.py` | Short-circuits for "recurring" tasks; scheduling not yet implemented |

#### `*_agent.py` — LangChain agents

Each agent is a LangChain `create_agent()` instance with tools bound and a system prompt loaded from `agents/prompts/`.

| Module | Agent variable | LLM | Tools |
|--------|---------------|-----|-------|
| `fundamental_agent.py` | `fundamental_analysis_agent` | `DATA_ANALYSIS_MODEL` (Claude Sonnet) | `get_financial_statements`, `get_stock_overview` |
| `sentiment_agent.py` | `sentiment_analysis_agent` | `MINI_MODEL` (GPT-mini) | `get_stock_news_feed`, `get_market_news_feed`, `fetch_article_content` |
| `option_agent.py` | `options_analysis_agent` | `DATA_ANALYSIS_MODEL` (Claude Sonnet) | `get_options_descriptive`, `option_max_pain_value`, `stock_option_liquidity`, `option_chain_top_oi`, `option_chain_filtered`, `option_chain_raw` |

#### `tools/` — LangChain `@tool` wrappers

Thin facades over `services/`. Every tool function has a docstring used as the LLM tool description. Tools **never** import from `data/` directly.

| Tool | Service call |
|------|-------------|
| `get_financial_statements` | `fundamental_service.fetch_financial_statements()` |
| `get_stock_overview` | `fundamental_service.fetch_stock_overview()` |
| `get_stock_news_feed` | `news_service.format_stock_news_feed()` |
| `get_market_news_feed` | `news_service.format_market_news_feed()` |
| `fetch_article_content` | `news_service.fetch_article_by_id()` |
| `get_options_descriptive` | `options_service.build_options_descriptive()` |
| `option_max_pain_value` | `options_service.compute_max_pain()` |
| `stock_option_liquidity` | `options_service.check_option_liquidity()` |
| `option_chain_top_oi` | `options_service.get_top_open_interest()` |
| `option_chain_filtered` | `options_service.get_filtered_option_chain()` |
| `option_chain_raw` | `options_service.get_raw_option_chain()` |

### `services/`

The business logic layer. Each service owns the composition of one domain area: it calls the data adapter and pipes results through the analysis layer.

| Module | Functions | Responsibilities |
|--------|-----------|-----------------|
| `fundamental_service.py` | `fetch_financial_statements()`, `fetch_stock_overview()`, `fetch_stock_descriptive()` | Wraps `data/finviz/fundamental.py`; used by agent tools and `SynthesizeNode` |
| `news_service.py` | `format_stock_news_feed()`, `format_market_news_feed()`, `fetch_article_by_id()` | Wraps `data/finviz/news.py` + article `registry` + `extractor` |
| `options_service.py` | `build_options_descriptive()`, `compute_max_pain()`, `check_option_liquidity()`, `get_top_open_interest()`, `get_filtered_option_chain()`, `get_raw_option_chain()` | Orchestrates chain fetching + all options calculation functions |

### `analysis/`

Pure calculation functions. No I/O, no framework dependencies. Input is a pandas `DataFrame`; output is a typed result or a formatted string.

#### `analysis/options/`

| Module | Key exports |
|--------|-------------|
| `common.py` | `FinvizOptionChainKeys`, `OptionLiquidityResult`, `OptionLiquidityScore`, `OptionMaxPainResult` |
| `gamma_exposure.py` | `gex_strike_table()`, `calculate_gamma_flip()` |
| `open_interest.py` | `top_open_interest()`, `calculate_call_put_activity()` |
| `implied_volatility.py` | `calculate_implied_volatility()` |
| `option_max_pain_value.py` | `calculate_max_pain()` |
| `is_option_chain_liquid.py` | `is_option_chain_liquid()` → `OptionLiquidityResult` |
| `get_expiration_date.py` | `get_n_nearest_expirations()`, `get_dte_for_expiration()`, `get_nearest_expiration()` |

#### `analysis/news/`

| Module | Key exports |
|--------|-------------|
| `extractor.py` | `extract_article(url)` — fetches and extracts clean article text (trafilatura + BS4 fallback) |
| `registry.py` | `register(url) → int`, `resolve(id) → str\|None`, `init()` — per-context article ID registry; keeps URLs out of the LLM context window |

### `data/finviz/`

Concrete Finviz Elite API adapter. All HTTP calls live here. Each function is decorated with `@redis_cache`.

| Module | Canonical functions | Cache TTL |
|--------|-------------------|-----------|
| `fundamental.py` | `get_fundamental_info()`, `get_stock_descriptive()` | 24h / 1h |
| `news.py` | `get_stock_news()`, `get_market_news()` | 5 min |
| `option_chain.py` | `get_option_chain()` | 5 min |
| `quote.py` | `get_stock_quote()` | — |
| `screener.py` | `get_hourly_oversold_screener()`, etc. | — |
| `client.py` | `with_api_token()`, `get_headers()` | — |

> `get_*.py` and `utils.py` are backward-compat shims that re-export from the canonical modules above.

### `infrastructure/`

| Module | Key export |
|--------|-----------|
| `cache/decorator.py` | `@redis_cache(ttl, dumps, loads)` — Redis-backed cache decorator; gracefully degrades when Redis is down |
| `cache/redis_client.py` | `get_redis()` — returns singleton `Redis` client or `None` |
| `cache/serializers.py` | `df_dumps`, `df_loads` — DataFrame ↔ string serializers for cache |
| `persistence/checkpointer.py` | `create_postgres_checkpointer()` — creates `AsyncPostgresSaver` backed by Supabase PostgreSQL |

### `observability/`

| Module | Key exports |
|--------|------------|
| `langfuse.py` | `get_langfuse_handler()` — creates a `CallbackHandler` per request; `flush_handler(handler)` — async flush without blocking the event loop |

### `ui/`

| Module | Role |
|--------|------|
| `chainlit_app.py` | Primary web UI. `@cl.on_message` drives `graph.astream_events()`, streams synthesis tokens to the browser, flushes Langfuse |
| `openwebui_pipeline.py` | OpenWebUI adapter. Runs the async graph on a background event loop; yields tokens via a sync generator (OpenWebUI's interface) |

---

## Class / Type Relations

```
TaskClassificationResult (domain/schemas.py)
  ├─ task_type: "immediate" | "recurring"
  ├─ invoke_agents: list["fundamental"|"sentiment"|"option"]
  ├─ agent_queries: dict[str, str]   ← per-agent refined query
  └─ ticker: str | None

AgentState (graph/state.py)  ← flows through every LangGraph node
  ├─ messages: list[BaseMessage]        add_messages reducer (append)
  ├─ previous_context: str              accumulated prior analyses
  ├─ query: str                         raw user input
  ├─ task_classification: TaskClassificationResult
  ├─ results: list[AgentOutput]         _results_reducer (reset | append)
  └─ final_answer: str

AgentOutput (graph/state.py)
  ├─ source: str    e.g. "Fundamental Analysis"
  └─ result: str    agent's markdown response

News (domain/models.py)
  ├─ title, date, url, ticker

StockDescriptiveInfo (domain/models.py)
  ├─ description: str
  ├─ financials: list[(label, value)]
  └─ institutional_ownership: list[(name, pct)]

OptionLiquidityResult (analysis/options/common.py)
  ├─ call_score: OptionLiquidityScore
  └─ put_score:  OptionLiquidityScore

OptionMaxPainResult (analysis/options/common.py)
  ├─ expiration: list[str]
  └─ max_pain_value: list[float]
```

---

## Typical Agent Pipeline

The following traces a full "immediate" multi-agent query:
**"Full analysis of AAPL — fundamentals, sentiment, and options."**

```
User  ──► UI (Chainlit / OpenWebUI)
           │
           │  graph.astream_events({
           │      "query": "...",
           │      "messages": [HumanMessage(...)],
           │      "results": []           ← reset signal
           │  }, config={thread_id, callbacks=[langfuse_handler]})
           │
           ▼
    ┌──────────────────┐
    │ task_classification│  MINI_MODEL (GPT-mini, fast/cheap)
    │  TaskClassification│  reads: query, messages, previous_context
    │  Node              │  writes: task_classification →
    └────────┬─────────┘    TaskClassificationResult{
             │                task_type="immediate",
             │                invoke_agents=["fundamental","sentiment","option"],
             │                agent_queries={...},
             │                ticker="AAPL"
             │              }
             │
    ┌────────▼──────────────────────────────────────────┐
    │  _route_task() → ["fundamental","sentiment","option"]│
    │  LangGraph fans out to all three nodes in parallel  │
    └────────┬──────────────────────────────────────────┘
             │
    ┌────────┴────────────────────────────────────────────────┐
    │        │                    │                           │
    ▼        ▼                    ▼                           ▼
┌──────────┐ ┌──────────────┐ ┌──────────────────────────────┐
│fundamental│ │  sentiment   │ │          option              │
│ Analysis  │ │  Analysis    │ │         Analysis             │
│  Node     │ │  Node        │ │          Node                │
└─────┬─────┘ └─────┬────────┘ └──────────────┬──────────────┘
      │             │                          │
      │  invokes    │  init_registry()         │  invokes
      │  fundamental│  invokes                 │  options_analysis
      │  _analysis  │  sentiment_analysis      │  _agent
      │  _agent     │  _agent                  │
      │             │                          │
      │  DATA_ANALYSIS_MODEL  MINI_MODEL        DATA_ANALYSIS_MODEL
      │  (Claude Sonnet)      (GPT-mini)        (Claude Sonnet)
      │             │                          │
      │  Tools used:│  Tools used:             │  Tools used:
      │  • get_      │  • get_stock_news_feed   │  • get_options_descriptive
      │    financial │  • get_market_news_feed  │  • option_max_pain_value
      │    _statements│ • fetch_article_content │  • stock_option_liquidity
      │  • get_stock │                          │  • option_chain_top_oi
      │    _overview │                          │  • option_chain_filtered
      │             │                          │  • option_chain_raw
      │             │                          │
      │  calls      │  calls                   │  calls
      │  services/  │  services/               │  services/
      │  fundamental│  news_service.py         │  options_service.py
      │  _service.py│                          │
      │             │                          │
      │  which calls│  which calls             │  which calls
      │  data/finviz│  data/finviz/news.py     │  data/finviz/
      │  /fundamental│ + analysis/news/        │  option_chain.py
      │  .py        │   registry.py            │  + analysis/options/
      │             │   extractor.py           │   *.py
      │  (Redis-    │  (Redis-cached 5 min)    │  (Redis-cached 5 min)
      │  cached 24h)│                          │
      │             │                          │
      ▼             ▼                          ▼
  AgentOutput   AgentOutput               AgentOutput
  {source:      {source:                  {source:
   "Fundamental  "Sentiment               "Option
    Analysis",    Analysis",               Analysis",
   result: ...}  result: ...}             result: ...}
      │             │                          │
      └─────────────┴──────────────────────────┘
                    │  state.results = [all three AgentOutputs]
                    ▼
            ┌───────────────┐
            │   synthesize  │  SMART_MODEL (GPT-5.4, high quality)
            │  SynthesizeNode│
            └───────┬───────┘
                    │  builds context:
                    │    1. fetch_stock_descriptive("AAPL")  ← fundamental_service
                    │    2. concatenate all AgentOutput.result strings
                    │
                    │  invokes llm_chain (PromptTemplate | LLM)
                    │  streams tokens → UI
                    │
                    │  writes:
                    │    final_answer: str
                    │    previous_context: prior + new analysis  (multi-turn memory)
                    ▼
                  END
                    │
             UI receives streamed tokens,
             appends AIMessage to graph state,
             flushes Langfuse handler
```

### Recurring task path

When `task_type == "recurring"`, the router sends to `RecurringTaskNode` instead, which short-circuits directly to `END` without calling any analysis agents or synthesis.

```
task_classification → recurring_task → END
```

### Follow-up query (no new agents needed)

When the user asks a follow-up on already-analysed data (e.g. "what about the dividend yield?"), the classifier may return `invoke_agents=[]`. The router then routes directly to `synthesize`, which answers from `previous_context` without any API calls.

```
task_classification → synthesize (from previous_context) → END
```

---

## Multi-turn Memory

`AgentState.previous_context` accumulates analysis text across turns within the same thread:

```
Turn 1:  previous_context = ""
         → analysis runs → previous_context = "--- Analysis: AAPL ---\n<answer>"

Turn 2:  previous_context = "<turn 1 answer>"
         → available to TaskClassificationNode (decides if agents needed)
         → available to SynthesizeNode (context for follow-up answer)
```

Thread identity is the `thread_id` in the LangGraph config, sourced from the user's session ID in Chainlit or `chat_id` in OpenWebUI. State is persisted to PostgreSQL via `AsyncPostgresSaver` between turns.

---

## Caching Strategy

| Data | TTL | Rationale |
|------|-----|-----------|
| Financial statements | 24 h | Quarterly filings — intraday freshness not needed |
| Stock descriptive / metrics | 1 h | Snapshot metrics change slowly during the day |
| News feeds | 5 min | News is time-sensitive; short TTL balances latency |
| Options chains | 5 min | Prices change tick by tick; short TTL keeps data usable |
| Fundamental tool results (agent layer) | 24 h / 1 h | Additional cache at the LangChain tool level |

Cache keys are `cache:{func_name}:{sha256(args)}`. Redis is optional — if unavailable the system runs without caching.

---

## LLM Routing Strategy

| Role | Model constant | Actual model | Rationale |
|------|---------------|-------------|-----------|
| Task classification | `MINI_MODEL` | `openai:gpt-5-mini` | Latency-critical router; structured output only |
| Sentiment agent | `MINI_MODEL` | `openai:gpt-5-mini` | News summarisation; lower complexity |
| Fundamental agent | `DATA_ANALYSIS_MODEL` | `claude-sonnet-4-6` | Deep financial reasoning |
| Options agent | `DATA_ANALYSIS_MODEL` | `claude-sonnet-4-6` | Complex numerical and strategic reasoning |
| Synthesis | `SMART_MODEL` | `openai:gpt-5.4` | Highest quality; final user-facing output |

---

## Deployment

```
docker-compose.yml
  redis-cache         :6379  — response cache (LRU eviction)
  trading-pipeline    :9099  — OpenWebUI Pipelines server
  openwebui           :8080  — chat UI

docker-compose.langfuse.yml
  langfuse-web        :3001  — observability dashboard
  langfuse-worker            — async trace processor
  postgres                   — Langfuse + LangGraph checkpointer storage
  clickhouse                 — time-series analytics
  redis                      — Langfuse session cache
  minio                      — object storage

Chainlit (dev / primary)
  just run            :8000
```

```
just run          # Chainlit web UI on :8000
just query "..."  # direct CLI query
just visualize    # export graph topology as PNG
just test         # pytest
just up / down    # Docker services (Redis + Langfuse)
```
