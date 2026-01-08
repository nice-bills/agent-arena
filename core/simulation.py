"""Main simulation engine for DeFi agent market."""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass

from core.agent import Agent
from core.defi_mechanics import Pool
from core.summarizer import Summarizer
from api.supabase_client import (
    SupabaseClient, RunData, AgentStateData, PoolStateData, ActionData, MetricsData
)
from config import NUM_AGENTS, TURNS_PER_RUN


@dataclass
class Simulation:
    """Orchestrates the DeFi agent simulation."""

    num_agents: int = NUM_AGENTS
    turns_per_run: int = TURNS_PER_RUN
    supabase: Optional[SupabaseClient] = None

    def __post_init__(self):
        self.agents: List[Agent] = []
        self.pool: Optional[Pool] = None
        self.current_run_id: Optional[int] = None
        self.current_run_number: int = 0

        if self.supabase is None:
            try:
                self.supabase = SupabaseClient()
            except ValueError:
                print("Warning: Supabase not configured. Running without persistence.")
                self.supabase = None

    def initialize_run(self, run_number: int = None):
        """Initialize a new run with agents and pool."""
        if run_number is None:
            if self.supabase:
                run_number = self.supabase.get_next_run_number()
            else:
                run_number = self.current_run_number + 1

        self.current_run_number = run_number
        self.agents = [Agent(f"Agent_{i}") for i in range(self.num_agents)]
        self.pool = Pool()

        print(f"Initialized run {run_number} with {self.num_agents} agents")

        if self.supabase:
            self.current_run_id = self.supabase.create_run(run_number)
            print(f"Created run in database: ID {self.current_run_id}")

    def run(self, run_number: int = None) -> Dict:
        """Execute a complete simulation run."""
        self.initialize_run(run_number)

        print(f"\nStarting run {self.current_run_number} with {self.turns_per_run} turns...")

        for turn in range(self.turns_per_run):
            print(f"\n--- Turn {turn + 1}/{self.turns_per_run} ---")

            # Each agent makes a decision
            for agent in self.agents:
                decision, thinking = self._agent_decide(agent, turn)

                # Execute action
                if decision:
                    success = agent.execute_action(decision, self.pool)
                    print(f"  {agent.name}: {decision.get('action', 'unknown')} {'OK' if success else 'FAIL'}")

                # Save action to database
                if self.supabase:
                    self._save_action(agent, turn, decision, thinking)

            # Save state snapshots
            if self.supabase:
                self._save_states(turn)

        # Calculate and save metrics
        metrics = self._calculate_metrics()

        if self.supabase:
            self.supabase.complete_run(self.current_run_id)
            self.supabase.save_metrics(
                MetricsData(
                    run_id=self.current_run_id,
                    gini_coefficient=metrics.get("gini_coefficient", 0),
                    cooperation_rate=metrics.get("cooperation_rate", 0),
                    betrayal_count=metrics.get("betrayal_count", 0),
                    avg_agent_profit=metrics.get("avg_agent_profit", 0),
                    pool_stability=metrics.get("pool_stability", 0)
                )
            )

            # Generate and save run summary
            try:
                summarizer = Summarizer(supabase=self.supabase)
                summary = summarizer.summarize_and_save(self.current_run_id)
                print(f"Generated summary for run {self.current_run_id}")
            except Exception as e:
                print(f"Warning: Failed to generate summary - {e}")

        # Update agent learning
        for agent in self.agents:
            agent.update_learning(self.current_run_number, metrics)

        print(f"\n--- Run {self.current_run_number} Complete ---")
        print(f"Final metrics: {json.dumps(metrics, indent=2)}")

        self.current_run_number += 1
        return metrics

    def _agent_decide(self, agent: Agent, turn: int) -> tuple:
        """Get decision from agent."""
        observation = {
            "turn": turn,
            "event": "trading"
        }
        pool_state = self.pool.get_state()

        try:
            decision, thinking = agent.decide(
                observation,
                pool_state,
                self.agents,
                turn
            )
            return decision, thinking
        except Exception as e:
            print(f"  {agent.name}: Decision error - {e}")
            return {"action": "do_nothing", "reasoning": f"Error: {e}"}, ""

    def _save_action(self, agent: Agent, turn: int, decision: Dict, thinking: str):
        """Save agent action to database."""
        self.supabase.save_action(ActionData(
            run_id=self.current_run_id,
            turn=turn,
            agent_name=agent.name,
            action_type=decision.get("action", "unknown"),
            payload=decision.get("payload", {}),
            reasoning_trace=decision.get("reasoning", ""),
            thinking_trace=thinking
        ))

    def _save_states(self, turn: int):
        """Save agent and pool states to database."""
        # Save agent states
        for agent in self.agents:
            self.supabase.save_agent_state(AgentStateData(
                run_id=self.current_run_id,
                turn=turn,
                agent_name=agent.name,
                token_a_balance=agent.token_a,
                token_b_balance=agent.token_b,
                profit=agent.calculate_profit(),
                strategy=agent.infer_strategy()
            ))

        # Save pool state
        self.supabase.save_pool_state(PoolStateData(
            run_id=self.current_run_id,
            turn=turn,
            reserve_a=self.pool.reserve_a,
            reserve_b=self.pool.reserve_b,
            price_ab=self.pool.price_ab,
            total_liquidity=self.pool.total_liquidity
        ))

    def _calculate_metrics(self) -> Dict:
        """Calculate run metrics."""
        if not self.agents:
            return {}

        profits = [a.calculate_profit() for a in self.agents]
        gini = self._gini_coefficient(profits)

        return {
            "gini_coefficient": gini,
            "avg_agent_profit": sum(profits) / len(profits),
            "cooperation_rate": self._calculate_cooperation(),
            "betrayal_count": self._count_betrayals(),
            "pool_stability": self.pool.reserve_a * self.pool.reserve_b
        }

    @staticmethod
    def _gini_coefficient(values: List[float]) -> float:
        """Calculate Gini coefficient for wealth distribution."""
        if not values or sum(values) == 0:
            return 0

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        cumsum = 0
        for i, val in enumerate(sorted_vals):
            cumsum += (i + 1) * val

        gini = (2 * cumsum) / (n * sum(sorted_vals)) - (n + 1) / n
        return max(0, gini)  # Ensure non-negative

    def _calculate_cooperation(self) -> float:
        """Calculate cooperation rate (alliances / agents)."""
        total_alliances = sum(len(a.alliances) for a in self.agents)
        return total_alliances / max(len(self.agents), 1)

    def _count_betrayals(self) -> int:
        """Count betrayal events (placeholder for future implementation)."""
        return 0


def test_simulation():
    """Test the simulation with a short run."""
    print("Testing Simulation class...")
    print("(Running without Supabase for quick test)\n")

    sim = Simulation(num_agents=3, turns_per_run=3, supabase=None)
    metrics = sim.run()

    print(f"\nFinal Metrics:")
    print(f"  Gini Coefficient: {metrics['gini_coefficient']:.4f}")
    print(f"  Avg Agent Profit: {metrics['avg_agent_profit']:.2f}")
    print(f"  Pool Stability: {metrics['pool_stability']:.2f}")

    # Show agent states
    print("\nFinal Agent States:")
    for agent in sim.agents:
        print(f"  {agent.name}: A={agent.token_a:.2f}, B={agent.token_b:.2f}, Profit={agent.calculate_profit():.2f}")

    print("\nSimulation test complete!")


if __name__ == "__main__":
    test_simulation()
