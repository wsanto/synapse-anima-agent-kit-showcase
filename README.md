# Synapse Anima Agent Kit (showcase excerpt)

An excerpt from a full-stack SDK (Python backend package + React frontend package + a standalone
FastAPI server) for embedding a conversational agent into a product. This repo shows the
**infrastructure layers on both sides of the stack** — auth, multi-backend storage abstraction, LLM
provider clients, the server/websocket transport, and the chat UI/SDK surface — as a demonstration
of full-stack SDK design, not the agent's actual cognitive architecture.

This is a curated excerpt, not the full kit: several modules import internals that live in the
private codebase, so this repo is for reading, not running.

## What's included here

**Python package (`packages/python/synapse_anima/`):**
- `auth/base.py` — auth abstraction
- `providers/` — LLM provider clients (`mistral.py`, `nous.py`) behind a common `base.py` interface
- `storage/` — a storage abstraction with three interchangeable backends: in-memory, Neo4j, and
  Supabase
- `server/` — the FastAPI app, websocket transport, and routing layer
- `config.py`, `types.py` — shared configuration and type definitions

**Standalone server (`server/`):** the top-level FastAPI entry point and auth middleware.

**React SDK (`packages/react/`):** `AnimaChat`/`AnimaProvider` (the SDK's public entry points),
chat UI components (message list, input, thinking indicator, a reasoning-chain display), a
structured-content renderer (paragraphs, headings, lists, code blocks, tables, callouts), mode
selector components, and the chat-related state stores/hooks.

## What was built but isn't shown here

The private repo includes the actual cognitive architecture this SDK exposes:

- **Agent core** (`agent.py`, `cognition.py`, `nexus.py`, `personality.py`) — orchestration and
  personality composition.
- **Emotion engine** — the emotional-intelligence modeling layer.
- **Beliefs, goals, interests, memory** — both the backend APIs and the corresponding React
  components/stores/hooks (belief cards, goal tracking, memory explorer/timeline, interest
  tracking, emotion analytics) that visualize this state — this is the product's actual
  differentiator, so it's withheld end-to-end, backend and frontend alike.
- **Tool-calling layer** bound to the memory system.
- Deployment/infrastructure config and internal planning docs.

I'm happy to walk through the design of any of these in conversation — they're just not published
as code.

## Stack

Python (FastAPI, websockets) backend package + React/TypeScript frontend SDK, with a pluggable
storage layer (in-memory / Neo4j / Supabase) and pluggable LLM providers.
