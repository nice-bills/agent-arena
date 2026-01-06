"""Supabase client for DeFi Agents simulation data persistence."""

from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from dataclasses import dataclass

from config import SUPABASE_URL, SUPABASE_KEY


@dataclass
class RunData:
    """Data class for run information."""
    run_number: int
    status: str = "running"
    mechanics: List[str] = None
    config: Dict = None

    def __post_init__(self):
        if self.mechanics is None:
            self.mechanics = []
        if self.config is None:
            self.config = {}


@dataclass
class AgentStateData:
    """Data class for agent state."""
    run_id: int
    turn: int
    agent_name: str
    token_a_balance: float = 0
    token_b_balance: float = 0
    profit: float = 0
    strategy: str = "unknown"


@dataclass
class PoolStateData:
    """Data class for pool state."""
    run_id: int
    turn: int
    reserve_a: float = 0
    reserve_b: float = 0
    price_ab: float = 0
    total_liquidity: float = 0


@dataclass
class ActionData:
    """Data class for agent action."""
    run_id: int
    turn: int
    agent_name: str
    action_type: str
    payload: Dict = None
    reasoning_trace: str = ""
    thinking_trace: str = ""

    def __post_init__(self):
        if self.payload is None:
            self.payload = {}


@dataclass
class MetricsData:
    """Data class for run metrics."""
    run_id: int
    gini_coefficient: float = 0
    cooperation_rate: float = 0
    betrayal_count: int = 0
    avg_agent_profit: float = 0
    pool_stability: float = 0


class SupabaseClient:
    """Client for interacting with Supabase database."""

    def __init__(self, url: str = None, key: str = None):
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY

        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials required. Set SUPABASE_URL and SUPABASE_KEY in .env"
            )

        self.client: Client = create_client(self.url, self.key)

    # ==================== RUNS ====================

    def create_run(self, run_number: int, config: Dict = None) -> int:
        """Create a new run and return its ID."""
        response = self.client.table("runs").insert({
            "run_number": run_number,
            "status": "running",
            "config": config or {}
        }).execute()

        return response.data[0]["id"]

    def get_run_by_number(self, run_number: int) -> Optional[Dict]:
        """Get run by run_number."""
        response = self.client.table("runs").select("*").eq("run_number", run_number).execute()
        return response.data[0] if response.data else None

    def update_run_status(self, run_id: int, status: str, end_time: bool = False):
        """Update run status."""
        update_data = {"status": status}
        if end_time:
            from datetime import datetime
            update_data["end_time"] = datetime.now().isoformat()

        self.client.table("runs").update(update_data).eq("id", run_id).execute()

    def complete_run(self, run_id: int):
        """Mark a run as completed."""
        self.update_run_status(run_id, "completed", end_time=True)

    def get_all_runs(self) -> List[Dict]:
        """Get all runs with their metrics."""
        response = self.client.table("runs").select("*").order("run_number", desc=True).execute()
        return response.data

    def get_next_run_number(self) -> int:
        """Get the next run number to use."""
        response = self.client.rpc("get_next_run_number").execute()
        return response.data if response.data else 1

    # ==================== AGENT STATES ====================

    def save_agent_state(self, data: AgentStateData):
        """Save agent state to database."""
        self.client.table("agent_states").insert({
            "run_id": data.run_id,
            "turn": data.turn,
            "agent_name": data.agent_name,
            "token_a_balance": data.token_a_balance,
            "token_b_balance": data.token_b_balance,
            "profit": data.profit,
            "strategy": data.strategy
        }).execute()

    def get_agent_states(self, run_id: int, turn: int = None) -> List[Dict]:
        """Get agent states for a run."""
        query = self.client.table("agent_states").select("*").eq("run_id", run_id)
        if turn is not None:
            query = query.eq("turn", turn)
        response = query.order("turn").order("agent_name").execute()
        return response.data

    def get_agent_states_by_name(self, run_id: int, agent_name: str) -> List[Dict]:
        """Get all states for a specific agent in a run."""
        response = self.client.table("agent_states").select("*").eq("run_id", run_id).eq("agent_name", agent_name).order("turn").execute()
        return response.data

    # ==================== POOL STATES ====================

    def save_pool_state(self, data: PoolStateData):
        """Save pool state to database."""
        self.client.table("pool_states").insert({
            "run_id": data.run_id,
            "turn": data.turn,
            "reserve_a": data.reserve_a,
            "reserve_b": data.reserve_b,
            "price_ab": data.price_ab,
            "total_liquidity": data.total_liquidity
        }).execute()

    def get_pool_states(self, run_id: int, turn: int = None) -> List[Dict]:
        """Get pool states for a run."""
        query = self.client.table("pool_states").select("*").eq("run_id", run_id)
        if turn is not None:
            query = query.eq("turn", turn)
        response = query.order("turn").execute()
        return response.data

    # ==================== ACTIONS ====================

    def save_action(self, data: ActionData):
        """Save agent action to database."""
        self.client.table("actions").insert({
            "run_id": data.run_id,
            "turn": data.turn,
            "agent_name": data.agent_name,
            "action_type": data.action_type,
            "payload": data.payload,
            "reasoning_trace": data.reasoning_trace,
            "thinking_trace": data.thinking_trace
        }).execute()

    def get_actions(self, run_id: int, turn: int = None) -> List[Dict]:
        """Get all actions for a run."""
        query = self.client.table("actions").select("*").eq("run_id", run_id)
        if turn is not None:
            query = query.eq("turn", turn)
        response = query.order("turn").order("agent_name").execute()
        return response.data

    def get_action_by_id(self, action_id: int) -> Optional[Dict]:
        """Get a specific action by ID."""
        response = self.client.table("actions").select("*").eq("id", action_id).execute()
        return response.data[0] if response.data else None

    def get_thinking_trace(self, action_id: int) -> Optional[str]:
        """Get the thinking trace for a specific action."""
        action = self.get_action_by_id(action_id)
        return action["thinking_trace"] if action else None

    # ==================== METRICS ====================

    def save_metrics(self, data: MetricsData):
        """Save run metrics to database."""
        self.client.table("run_metrics").insert({
            "run_id": data.run_id,
            "gini_coefficient": data.gini_coefficient,
            "cooperation_rate": data.cooperation_rate,
            "betrayal_count": data.betrayal_count,
            "avg_agent_profit": data.avg_agent_profit,
            "pool_stability": data.pool_stability
        }).execute()

    def get_metrics(self, run_id: int) -> Optional[Dict]:
        """Get metrics for a specific run."""
        response = self.client.table("run_metrics").select("*").eq("run_id", run_id).execute()
        return response.data[0] if response.data else None

    # ==================== RUN DETAILS ====================

    def get_run_detail(self, run_id: int) -> Dict[str, List[Dict]]:
        """Get complete details for a run (actions, agents, pool)."""
        actions = self.get_actions(run_id)
        agents = self.get_agent_states(run_id)
        pool = self.get_pool_states(run_id)
        metrics = self.get_metrics(run_id)

        return {
            "actions": actions,
            "agent_states": agents,
            "pool_states": pool,
            "metrics": metrics
        }

    # ==================== UTILITY ====================

    def health_check(self) -> bool:
        """Check if Supabase connection is healthy."""
        try:
            response = self.client.table("runs").select("id").limit(1).execute()
            return True
        except Exception:
            return False


def test_client():
    """Test the Supabase client."""
    try:
        client = SupabaseClient()
        print("Supabase client initialized successfully!")

        # Health check
        if client.health_check():
            print("✓ Connection healthy")
        else:
            print("✗ Connection failed")

        # Try to get runs
        runs = client.get_all_runs()
        print(f"✓ Retrieved {len(runs)} runs")

    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_client()
