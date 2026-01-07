"""FastAPI backend for DeFi Agents simulation dashboard."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from api.supabase_client import SupabaseClient
from core.simulation import Simulation
from core.analyzer import Analyzer

app = FastAPI(
    title="DeFi Agents API",
    description="Multi-agent LLM simulation in DeFi markets",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
supabase = None
try:
    supabase = SupabaseClient()
except ValueError:
    print("Warning: Supabase not configured")


# ==================== Pydantic Models ====================

class RunRequest(BaseModel):
    num_agents: int = 5
    turns_per_run: int = 10


class RunResponse(BaseModel):
    run_number: int
    metrics: Dict[str, Any]
    agents: List[Dict[str, Any]]


class AgentActionRequest(BaseModel):
    agent_name: str
    action: str
    payload: Dict = {}


# ==================== Root Endpoint ====================

@app.get("/")
def root():
    """Root endpoint - shows API info and links."""
    return {
        "name": "Agent Arena API",
        "description": "Multi-agent LLM simulation in DeFi markets",
        "version": "0.1.0",
        "links": {
            "docs": "/docs",
            "health": "/health",
            "runs": "/api/runs",
            "trends": "/api/analysis/trends"
        },
        "usage": {
            "start_run": "POST /api/runs with {\"num_agents\": 5, \"turns_per_run\": 10}",
            "list_runs": "GET /api/runs",
            "view_run": "GET /api/runs/{id}"
        }
    }


# ==================== Health Endpoints ====================

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "supabase": "connected" if supabase and supabase.health_check() else "disconnected"
    }


# ==================== Run Endpoints ====================

@app.post("/api/runs")
def create_run(request: RunRequest):
    """Start a new simulation run."""
    try:
        sim = Simulation(
            num_agents=request.num_agents,
            turns_per_run=request.turns_per_run,
            supabase=supabase
        )

        metrics = sim.run()

        # Get agent states
        agent_data = []
        for agent in sim.agents:
            agent_data.append({
                "name": agent.name,
                "token_a": agent.token_a,
                "token_b": agent.token_b,
                "profit": agent.calculate_profit(),
                "strategy": agent.infer_strategy()
            })

        return RunResponse(
            run_number=sim.current_run_number - 1,
            metrics=metrics,
            agents=agent_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs")
def get_all_runs():
    """Get all runs."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        runs = supabase.get_all_runs()
        return {"runs": runs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}")
def get_run_detail(run_id: int):
    """Get detailed run data."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        detail = supabase.get_run_detail(run_id)
        return detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Metrics Endpoints ====================

@app.get("/api/metrics/{run_id}")
def get_run_metrics(run_id: int):
    """Get metrics for a specific run."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        metrics = supabase.get_metrics(run_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Run not found")
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/trends")
def get_trends():
    """Get trend analysis across all runs."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        runs = supabase.get_all_runs()
        run_data = [r for r in runs if r.get("status") == "completed"]

        metrics = []
        for r in run_data:
            run_metrics = supabase.get_metrics(r["id"])
            if run_metrics:
                metrics.append(run_metrics)

        trends = Analyzer.detect_trends(metrics)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Thinking/Reasoning Endpoints ====================

@app.get("/api/thinking/{action_id}")
def get_thinking_trace(action_id: int):
    """Get the thinking trace for a specific action."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        thinking = supabase.get_thinking_trace(action_id)
        if thinking is None:
            raise HTTPException(status_code=404, detail="Action not found")
        return {"thinking": thinking}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analysis Endpoints ====================

@app.get("/api/analysis/arms-race/{run_id}")
def get_arms_race_analysis(run_id: int):
    """Detect arms race patterns in a run."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        actions = supabase.get_actions(run_id)
        analysis = Analyzer.detect_arms_races(actions)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    print("Starting DeFi Agents API server on http://0.0.0.0:8000")
    run_server()
