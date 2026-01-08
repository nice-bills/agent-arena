"""Run summarizer agent using MiniMax LLM."""

from typing import Dict, List, Any
from api.minimax_client import MiniMaxClient
from api.supabase_client import SupabaseClient, SummaryData


class Summarizer:
    """Agent that generates detailed summaries of simulation runs."""

    def __init__(self, supabase: SupabaseClient = None):
        self.supabase = supabase
        self.minimax = MiniMaxClient()

    def generate_summary(self, run_id: int) -> str:
        """Generate a detailed summary for a run."""
        # Get run data
        run_detail = self.supabase.get_run_detail(run_id)
        metrics = run_detail.get("metrics", {})
        actions = run_detail.get("actions", [])
        agent_states = run_detail.get("agent_states", [])
        pool_states = run_detail.get("pool_states", [])

        # Get run info
        runs = self.supabase.get_all_runs()
        run_info = next((r for r in runs if r["id"] == run_id), {})
        run_number = run_info.get("run_number", run_id)

        # Analyze data
        agent_performance = self._analyze_agents(agent_states)
        action_distribution = self._analyze_actions(actions)
        market_events = self._analyze_market_events(actions, pool_states)

        # Build prompt
        prompt = self._build_summary_prompt(
            run_number=run_number,
            metrics=metrics,
            agent_performance=agent_performance,
            action_distribution=action_distribution,
            market_events=market_events
        )

        # Generate summary using LLM
        response = self.minimax.complete(prompt, max_tokens=1024)

        return response.strip()

    def _analyze_agents(self, agent_states: List[Dict]) -> List[Dict]:
        """Analyze agent performance."""
        # Get latest state for each agent
        latest_by_agent = {}
        for state in agent_states:
            agent = state["agent_name"]
            if agent not in latest_by_agent or state["turn"] > latest_by_agent[agent]["turn"]:
                latest_by_agent[agent] = state

        performance = []
        for agent, state in latest_by_agent.items():
            performance.append({
                "name": agent,
                "profit": state.get("profit", 0),
                "strategy": state.get("strategy", "unknown"),
                "final_tokens": f"{state.get('token_a_balance', 0):.0f}A / {state.get('token_b_balance', 0):.0f}B"
            })

        # Sort by profit descending
        performance.sort(key=lambda x: x["profit"], reverse=True)
        return performance

    def _analyze_actions(self, actions: List[Dict]) -> Dict[str, int]:
        """Count action types."""
        distribution = {}
        for action in actions:
            action_type = action.get("action_type", "unknown")
            distribution[action_type] = distribution.get(action_type, 0) + 1
        return distribution

    def _analyze_market_events(self, actions: List[Dict], pool_states: List[Dict]) -> List[str]:
        """Identify notable market events."""
        events = []

        # Find significant pool changes
        if len(pool_states) >= 2:
            first_reserve = pool_states[0]
            last_reserve = pool_states[-1]

            if first_reserve and last_reserve:
                reserve_a_change = last_reserve["reserve_a"] - first_reserve["reserve_a"]
                reserve_b_change = last_reserve["reserve_b"] - first_reserve["reserve_b"]

                if abs(reserve_a_change) > 100 or abs(reserve_b_change) > 100:
                    events.append(f"Pool shifted: A {reserve_a_change:+.0f}, B {reserve_b_change:+.0f}")

        # Count alliances
        alliances = [a for a in actions if a.get("action_type") == "propose_alliance"]
        if len(alliances) > 3:
            events.append(f"{len(alliances)} alliance proposals made")

        # Count trades
        trades = [a for a in actions if a.get("action_type") == "swap"]
        if len(trades) > 5:
            events.append(f"{len(trades)} swap transactions executed")

        return events[:5]  # Limit to top 5 events

    def _build_summary_prompt(
        self,
        run_number: int,
        metrics: Dict,
        agent_performance: List[Dict],
        action_distribution: Dict[str, int],
        market_events: List[str]
    ) -> str:
        """Build the summary prompt for the LLM."""

        top_agents = agent_performance[:3] if agent_performance else []
        bottom_agents = agent_performance[-2:] if len(agent_performance) > 2 else []

        prompt = f"""Generate a detailed summary of this DeFi agent simulation run.

## Run {run_number} Summary

### Overall Metrics
- Gini Coefficient: {metrics.get('gini_coefficient', 0):.4f} (0=equal, 1=unequal)
- Average Agent Profit: {metrics.get('avg_agent_profit', 0):.2f}
- Cooperation Rate: {metrics.get('cooperation_rate', 0):.1f}%
- Pool Stability: {metrics.get('pool_stability', 0):.0f}

### Agent Performance (ranked by profit)
"""

        for i, agent in enumerate(top_agents, 1):
            prompt += f"{i}. {agent['name']}: {agent['profit']:+.2f} profit ({agent['strategy']})\n"

        if bottom_agents and bottom_agents != top_agents:
            prompt += "\nBottom performers:\n"
            for agent in bottom_agents:
                prompt += f"- {agent['name']}: {agent['profit']:+.2f} ({agent['strategy']})\n"

        prompt += f"\n### Action Distribution\n"
        for action_type, count in sorted(action_distribution.items(), key=lambda x: -x[1]):
            prompt += f"- {action_type}: {count}\n"

        if market_events:
            prompt += "\n### Notable Market Events\n"
            for event in market_events:
                prompt += f"- {event}\n"

        prompt += """
### Analysis
Write a 2-3 paragraph analysis covering:
1. Overall market behavior and whether agents cooperated or competed
2. Notable strategy patterns and their effectiveness
3. Key insights about the DeFi market dynamics

Keep the tone informative and analytical. Use markdown formatting for readability.
"""

        return prompt

    def summarize_and_save(self, run_id: int) -> Dict:
        """Generate summary and save to database."""
        summary_text = self.generate_summary(run_id)

        # Save to database
        summary_data = SummaryData(run_id=run_id, summary_text=summary_text)
        self.supabase.save_run_summary(summary_data)

        return {
            "run_id": run_id,
            "summary": summary_text
        }
