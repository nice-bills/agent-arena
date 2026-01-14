"""FastAPI backend for DeFi Agents simulation dashboard."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import traceback

from api.supabase_client import SupabaseClient
from core.simulation import Simulation
from core.analyzer import Analyzer
from core.summarizer import Summarizer

app = FastAPI(
    title="DeFi Agents API",
    description="Multi-agent LLM simulation in DeFi markets",
    version="0.1.0"
)


# Global exception handler for better error messages
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    tb_str = traceback.format_exception(type(exc), exc, exc.__traceback__)
    print(f"[GLOBAL ERROR] {error_msg}")
    print("".join(tb_str))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": error_msg,
            "type": type(exc).__name__
        }
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
    import traceback

    sim = None
    run_id = None

    print(f"[DEBUG] create_run: supabase={'connected' if supabase else 'None'}")

    try:
        sim = Simulation(
            num_agents=request.num_agents,
            turns_per_run=request.turns_per_run,
            supabase=supabase
        )

        print(f"[DEBUG] After Simulation init: sim.supabase={'yes' if sim.supabase else 'NO'}")

        # Store run_id for error recovery
        run_id = sim.current_run_id

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

    except TimeoutError as e:
        error_msg = str(e)
        print(f"[ERROR] Run timed out: {error_msg}")

        if run_id and supabase:
            try:
                supabase.update_run_status(run_id, "timeout")
                print(f"[ERROR] Marked run {run_id} as timeout")
            except:
                pass

        raise HTTPException(status_code=504, detail=f"Run timed out: {error_msg}")

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Run failed: {error_msg}")
        traceback.print_exc()

        # Try to mark run as failed if we have a run_id
        if run_id and supabase:
            try:
                supabase.update_run_status(run_id, "failed")
                print(f"[ERROR] Marked run {run_id} as failed")
            except:
                pass

        # Include more detail in error for debugging
        import traceback as tb
        detail = f"Run failed: {error_msg}"
        if "MiniMax" in error_msg or "API" in error_msg or "API key" in error_msg:
            detail += " (MiniMax API error - check API key configuration)"
        raise HTTPException(status_code=500, detail=detail)


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


@app.post("/api/admin/clear-stuck-runs")
def clear_stuck_runs():
    """Clear all runs marked as 'running' - marks them as failed."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        from datetime import datetime
        # Get all running runs
        runs = supabase.get_all_runs()
        stuck_runs = [r for r in runs if r.get("status") == "running"]

        updated = 0
        for run in stuck_runs:
            supabase.client.table("runs").update({
                "status": "failed",
                "end_time": datetime.now().isoformat()
            }).eq("id", run["id"]).execute()
            updated += 1

        return {"cleared": updated, "message": f"Marked {updated} stuck runs as failed"}
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


@app.get("/api/analysis/actions")
def get_action_distribution():
    """Get action distribution across all runs."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        runs = supabase.get_all_runs()
        completed_runs = [r for r in runs if r.get("status") == "completed"]

        action_counts = {}
        for run in completed_runs:
            actions = supabase.get_all_actions(run["id"])
            for action in actions:
                action_type = action.get("action_type", "unknown")
                # Filter out bonus actions for cleaner chart
                if not action_type.endswith("_bonus") and action_type != "alliance_success":
                    action_counts[action_type] = action_counts.get(action_type, 0) + 1

        data = [{"action_type": k, "count": v} for k, v in action_counts.items()]
        data.sort(key=lambda x: x["count"], reverse=True)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/chaos-events")
def get_chaos_events():
    """Get MarketMaker and ChaosAgent events."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        runs = supabase.get_all_runs()
        completed_runs = [r for r in runs if r.get("status") == "completed"]

        events = []
        for run in completed_runs:
            actions = supabase.get_all_actions(run["id"])
            for action in actions:
                action_type = action.get("action_type", "")
                if "marketmaker" in action_type.lower() or "chaos" in action_type.lower() or "price_shock" in action_type.lower():
                    events.append({
                        "run_id": run.get("run_number"),
                        "turn": action.get("turn"),
                        "action_type": action_type,
                        "reasoning": action.get("reasoning_trace", "")[:100],
                        "payload": action.get("payload", {})
                    })

        # Sort by run, then by turn
        events.sort(key=lambda x: (x["run_id"], x["turn"]), reverse=True)
        return {"data": events[:50]}
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


# ==================== Summary Endpoints ====================

@app.get("/api/runs/{run_id}/summary")
def get_run_summary(run_id: int):
    """Get summary for a specific run."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        summary = supabase.get_run_summary(run_id)
        if not summary:
            return {"run_id": run_id, "summary": None, "message": "No summary generated yet"}
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summaries")
def get_all_summaries():
    """Get all run summaries."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        summaries = supabase.get_all_summaries()
        return {"summaries": summaries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/runs/{run_id}/generate-summary")
def generate_run_summary(run_id: int):
    """Generate and save a summary for a run."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        summarizer = Summarizer(supabase=supabase)
        result = summarizer.summarize_and_save(run_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Agent Profit Endpoints ====================

@app.get("/api/agents")
def get_all_agents():
    """Get all unique agent names."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        agents = supabase.get_all_agent_names()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_name}/profits")
def get_agent_profits(agent_name: str):
    """Get profit history for an agent across all runs."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        profits = supabase.get_agent_profits_all_runs(agent_name)

        # Format for chart: [{run: 1, profit: 0, turn: 0}, ...]
        chart_data = []
        for p in profits:
            chart_data.append({
                "run": p["run_id"],
                "turn": p["turn"],
                "profit": p["profit"],
                "strategy": p.get("strategy", "unknown")
            })

        return {
            "agent_name": agent_name,
            "data": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/all-profits")
def get_all_agents_profits():
    """Get profit history for ALL agents across all runs - combined for charting."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        agents = supabase.get_all_agent_names()
        all_profits = {}

        for agent_name in agents:
            profits = supabase.get_agent_profits_all_runs(agent_name)
            for p in profits:
                run_id = p["run_id"]
                if run_id not in all_profits:
                    all_profits[run_id] = {"run": run_id}
                all_profits[run_id][agent_name] = p["profit"]

        # Convert to array and sort by run
        chart_data = sorted(all_profits.values(), key=lambda x: x["run"])

        return {
            "agents": agents,
            "data": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/version")
def get_version():
    """Get server version and git info."""
    import subprocess
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return {
            "commit": commit.stdout.strip()[:8],
            "branch": branch.stdout.strip(),
            "status": "running"
        }
    except Exception:
        return {"commit": "unknown", "branch": "unknown", "status": "running"}


@app.post("/api/restart")
def restart_server():
    """
    Signal the server to restart.
    For HuggingFace Spaces, this works with their restart mechanism.
    """
    import os
    import signal

    # Set environment variable to signal restart
    os.environ["RESTART_REQUESTED"] = "1"

    # Get PID for graceful shutdown
    pid = os.getpid()

    return {"status": "restarting", "message": "Restart signal sent", "pid": pid}


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    print("Starting DeFi Agents API server on http://0.0.0.0:8000")
    run_server()
