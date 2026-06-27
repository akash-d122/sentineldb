# SentinelDB Architecture Decisions

Use this file to record decisions that affect architecture, safety, scope, or implementation.

---

## ADR-001: Build evidence-first, LLM-second

**Date:** June 2026  
**Status:** Accepted

### Context
The product goal is incident analysis that DBEs can trust. A model-written essay can hallucinate metrics or hide uncertainty.

### Decision
Collectors and deterministic rules produce the evidence and selected candidate cause. The LLM may only compress the selected cause into a concise sentence. Evidence bullets are rendered by the system, not the LLM.

### Consequences
- More reliable reports.
- Easier tests.
- Less impressive demo text, but more trustworthy engineering output.

---

## ADR-002: Guardrails before collectors and dashboard

**Date:** June 2026  
**Status:** Accepted

### Context
The project touches database diagnostics. Safety is the main differentiator.

### Decision
The first implementation milestone is the guardrail checker and approved diagnostic catalog.

### Consequences
- Slower visible demo progress.
- Stronger foundation.
- Avoids unsafe agent behavior.

---

## ADR-003: V1A is local and deterministic

**Date:** June 2026  
**Status:** Accepted

### Context
CloudWatch, PMM, ticketing, and dashboard integrations add complexity.

### Decision
V1A will prove the core RCA pipeline locally before external integrations.

### Consequences
- Faster proof of life.
- Easier debugging.
- Cleaner portfolio story.

---

## ADR-004: Celery + Redis for async task processing

**Date:** June 2026  
**Status:** Accepted

### Context
FastAPI BackgroundTasks paired with a job table is sufficient for a minimal MVP, but lacks horizontal scaling and durable retry mechanics built-in. SentinelDB is a portfolio piece intended to demonstrate production system design.

### Decision
Use Celery + Redis from day 1 for async incident analysis processing.

### Consequences
- Establishes a production-grade async foundation immediately.
- Avoids an architectural refactor later.
- Adds Redis as a local development dependency.

---

## ADR-005: LiteLLM as LLM abstraction

**Date:** June 2026  
**Status:** Accepted

### Context
Direct vendor SDKs (e.g., Google GenAI, OpenAI) lock the codebase into specific provider interfaces, making it harder to test local models (Ollama) or switch cloud providers (Groq) for rate limits or cost.

### Decision
Use LiteLLM as the LLM abstraction layer for provider-agnostic access.

### Consequences
- Switching providers requires only a config string change.
- Automatic retries and token counting provided out-of-the-box.
- No vendor SDK lock-in.

---

## ADR-006: Gemini 2.5 Flash-Lite as primary LLM

**Date:** June 2026  
**Status:** Accepted

### Context
The LLM is used only for concise summarization of structured evidence, which does not require frontier-class reasoning. Cost and free-tier access are important for demo stability.

### Decision
Use Gemini 2.5 Flash-Lite via Google AI Studio as the primary LLM provider.

### Consequences
- Best free tier availability ($0.10/1M input, $0.40/1M output).
- Gemini 2.0 Flash was deprecated June 2026, making 2.5 Flash-Lite the cost-optimized choice.
- Sufficient hybrid reasoning for summarization constraints.

---

## ADR-007: SQLAlchemy 2.0 (async) + Alembic

**Date:** June 2026  
**Status:** Accepted

### Context
We need async-native database access and a migration path that ensures local Docker development stays identical to future cloud deployment (e.g., Supabase).

### Decision
Use SQLAlchemy 2.0 in async mode with Alembic for ORM and migrations, designing the schema with standard PostgreSQL features only.

### Consequences
- True async IO for the backend.
- Mature schema migration support.
- Standard PostgreSQL schema deploys to Supabase without any Supabase client library or vendor-specific API dependencies.

---

## ADR-008: LangGraph deferred to V2

**Date:** June 2026  
**Status:** Accepted

### Context
LangGraph provides powerful state graph orchestration for agents, but SentinelDB V1's analysis pipeline is deterministic, linear, and doesn't require branching, loops, or human-in-the-loop steps.

### Decision
Defer LangGraph wrapping to V2. Keep V1 interfaces (collector → analyzer → renderer) simple and linear.

### Consequences
- Avoids speculative over-engineering in V1.
- Clean boundaries ensure the pipeline can be wrapped in a LangGraph graph later if needed without refactoring core components.
