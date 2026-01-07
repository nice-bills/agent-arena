---
title: Agent Arena
emoji: 🌍
colorFrom: green
colorTo: gray
sdk: docker
short_description: LLM-powered agents compete in an automated DeFi market
---

# Agent Arena

Multi-agent LLM simulation in DeFi markets with emergent strategic arms races.

## Overview

Agent Arena is a simulation where AI agents powered by MiniMax-M2.1 compete in an automated DeFi market. Agents make strategic trading decisions, form alliances, and their behaviors evolve over time.

## Features

- AI agents powered by MiniMax-M2.1 with reasoning transparency
- Constant product AMM pool mechanics (like Uniswap)
- Real-time metrics including Gini coefficient, cooperation rates, and pool stability
- Strategic decision making with thinking traces
- Persistent storage with Supabase

## Architecture

```
defi-agents/
├── api/              # API clients (MiniMax, Supabase)
├── core/             # Core simulation (Agent, Pool, Simulation, Analyzer)
├── web/              # FastAPI backend
├── frontend/         # React dashboard (Vite + Tailwind)
├── scripts/          # Database schema
└── config.py         # Configuration
```

## Getting Started

### Prerequisites

- Python 3.11+
- uv (Python package manager)
- MiniMax API key
- Supabase project

### Installation

```bash
# Clone the repository
git clone https://github.com/nice-bills/agent-arena.git
cd agent-arena

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running Locally

```bash
# Start the backend
uv run python web/app.py

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/runs | Start a new simulation run |
| GET | /api/runs | List all runs |
| GET | /api/runs/{id} | Get run details |
| GET | /api/analysis/trends | Get trend analysis |
| GET | /api/thinking/{action_id} | Get thinking trace |

## Environment Variables

| Variable | Description |
|----------|-------------|
| MINIMAX_API_KEY | MiniMax API key |
| SUPABASE_URL | Supabase project URL |
| SUPABASE_KEY | Supabase anon key |
| NUM_AGENTS | Number of agents per run (default: 5) |
| TURNS_PER_RUN | Turns per simulation (default: 10) |

## License

MIT
