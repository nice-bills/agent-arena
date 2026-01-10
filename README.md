---
title: Agent Arena
emoji: 🌍
colorFrom: green
colorTo: gray
sdk: docker
short_description: LLM-powered agents compete in an automated DeFi market
---

# Agent Arena

Multi-agent LLM simulation in DeFi markets with emergent strategic behaviors.

## Overview

AI agents powered by MiniMax-M2.1 compete in an automated DeFi market. Agents trade, provide liquidity, form alliances, and their behaviors evolve. New incentive mechanics force action to prevent stagnation.

## What's New

### Agent Incentives (v1.1)

- **Boredom Penalty**: Agents lose 10 tokens after 1+ consecutive do_nothing actions
- **Alliance Bonuses**: Mutual alliance proposals grant +15 tokens to both agents
- **Market Maker**: Creates volatility every 3 turns with 15% trades
- **Price Shocks**: Random +/-10% price events create trading opportunities

### Auto-Deploy (v1.2)

- GitHub Actions automatically restart HF Space after code pushes
- `/api/version` endpoint shows current git commit
- `/api/restart` endpoint triggers manual restart

## Features

- AI agents powered by MiniMax-M2.1 with reasoning transparency
- Constant product AMM pool mechanics (like Uniswap)
- Real-time metrics: Gini coefficient, cooperation rates, pool stability
- Strategic decision making with thinking traces
- Persistent storage with Supabase
- Windows 95/2000 retro UI dashboard

## Architecture

```
defi-agents/
├── api/              # API clients (MiniMax, Supabase)
├── core/             # Core simulation (Agent, Pool, Simulation, Summarizer)
├── web/              # FastAPI backend
├── frontend/         # React dashboard (Vite + Tailwind)
├── supabase/         # Database migrations
├── scripts/          # Utility scripts
└── .github/workflows/ # CI/CD (scheduler + deploy)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/runs | Start new simulation |
| GET | /api/runs | List all runs |
| GET | /api/runs/{id} | Get run details |
| GET | /api/runs/{id}/summary | Get LLM summary |
| GET | /api/analysis/trends | Get trend analysis |
| GET | /api/agents/all-profits | All agents profit history |
| GET | /api/version | Get git commit |
| POST | /api/restart | Restart the server |

## Deployment

### HuggingFace Space

The app deploys to: https://nice-bill-agent-arena.hf.space

**Auto-Deploy Setup:**

1. Add `HF_TOKEN` secret in GitHub (Settings → Secrets → Actions)
2. Push to main → `deploy.yml` runs automatically
3. Workflow pushes to HF Space and calls `/api/restart`

### Cron Schedule

Runs every 6 hours via GitHub Actions:
```yaml
schedule:
  - cron: '0 */6 * * *'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| MINIMAX_API_KEY | MiniMax API key |
| SUPABASE_URL | Supabase project URL |
| SUPABASE_KEY | Supabase anon key |
| GROQ_API_KEY | Groq API key (optional, for free models) |
| HF_TOKEN | HuggingFace token (for auto-deploy) |
| HF_SPACE_URL | HF Space URL (for workflows) |

## Local Development

```bash
# Clone and install
git clone https://github.com/nice-bills/agent-arena.git
cd agent-arena
uv sync

# Start backend
uv run python web/app.py

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## License

MIT
