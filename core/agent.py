"""Agent class for DeFi simulation."""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from api.minimax_client import MiniMaxClient
from config import INITIAL_TOKENS


@dataclass
class Agent:
    """DeFi trading agent powered by MiniMax."""

    name: str
    token_a: float = INITIAL_TOKENS
    token_b: float = INITIAL_TOKENS
    trade_history: List[Dict] = field(default_factory=list)
    learning_summary: str = ""
    alliances: Dict[str, str] = field(default_factory=dict)
    consecutive_inaction: int = 0  # Track boredom
    total_boredom_penalty: float = 0  # Accumulated penalty

    # Boredom penalty config - MORE AGGRESSIVE
    BOREDOM_THRESHOLD: int = 1  # Start penalizing after 1 inaction (immediate!)
    BOREDOM_PENALTY_PER_TURN: float = 10.0  # Lose 10 tokens per turn of inaction

    def __post_init__(self):
        self.client = MiniMaxClient()

    def get_state(self) -> Dict:
        """Get current state for decision making."""
        return {
            "name": self.name,
            "token_a": round(self.token_a, 2),
            "token_b": round(self.token_b, 2),
            "profit": round(self.calculate_profit(), 2),
            "alliances": self.alliances,
            "consecutive_inaction": self.consecutive_inaction,
            "boredom_penalty": round(self.total_boredom_penalty, 2)
        }

    def decide(self, observation: Dict, pool_state: Dict, other_agents: List["Agent"], turn: int) -> Tuple[Dict, str]:
        """
        Ask MiniMax for a decision based on current state.

        Returns:
            Tuple of (decision_dict, thinking_text)
        """
        prompt = self._build_prompt(observation, pool_state, other_agents, turn)

        system_prompt = """You are a strategic DeFi trader in an automated market simulation.
Analyze the market state and make optimal trading decisions.
Output ONLY valid JSON with your reasoning."""

        decision, thinking = self.client.call(prompt, system_prompt)

        # Log the decision
        self.trade_history.append({
            "turn": turn,
            "action": decision.get("action", decision.get("action_type", "unknown")),
            "reasoning": decision.get("reasoning", ""),
            "thinking": thinking
        })

        return decision, thinking

    def _build_prompt(self, observation: Dict, pool_state: Dict, other_agents: List["Agent"], turn: int) -> str:
        """Build the decision prompt."""
        other_states = [a.get_state() for a in other_agents if a.name != self.name]

        # Find allied agents
        allied_names = [name for name, status in self.alliances.items() if status == 'success']
        allied_info = ""
        if allied_names:
            allied_info = f"\nYour ALLIES: {', '.join(allied_names)} - Coordinate with them for BONUS REWARDS!"

        # Boredom warning
        boredom_warning = ""
        if self.consecutive_inaction >= self.BOREDOM_THRESHOLD:
            penalty = (self.consecutive_inaction - self.BOREDOM_THRESHOLD + 1) * self.BOREDOM_PENALTY_PER_TURN
            boredom_warning = f"""
!!! URGENT: You have been inactive for {self.consecutive_inaction} consecutive turns.
You are losing {penalty:.1f} tokens per turn due to boredom penalty.
ACT NOW to avoid further losses!"""

        prompt = f"""
You are {self.name}, an AI agent in a DeFi market simulation.

=== YOUR STATE ===
Token A: {self.token_a:.2f}
Token B: {self.token_b:.2f}
Profit: {self.calculate_profit():.2f}
Consecutive inaction: {self.consecutive_inaction}
{allied_info}
{boredom_warning}

=== MARKET STATE ===
Pool reserves: A={pool_state.get('reserve_a', 0):.2f}, B={pool_state.get('reserve_b', 0):.2f}
Price (A/B): {pool_state.get('price_ab', 0):.4f}
Total liquidity: {pool_state.get('total_liquidity', 0):.2f}

=== OTHER AGENTS ===
{json.dumps(other_states, indent=2)}

=== YOUR LEARNING ===
{self.learning_summary if self.learning_summary else "No previous runs yet."}

=== REWARDS FOR ACTIONS ===
- SWAP: Active trading +3 tokens, profitable swap +5 extra!
- PROVIDE_LIQUIDITY: Earns fees from all swaps, +8 bonus tokens
- PROPOSE_ALLIANCE: If they accept, you BOTH get +4 bonus tokens
- COORDINATED TRADES: Trade during volatility +5 bonus tokens!
- POSITIVE PROFIT: End turn with profit = +10 bonus tokens!

=== AVAILABLE ACTIONS ===
1. "swap": Trade tokens (specify from, to, amount) - ACTIVE TRADING
2. "provide_liquidity": Add liquidity to pool (specify amounts) - EARNS FEES + BONUS
3. "propose_alliance": Suggest collaboration (specify agent name) - CAN GIVE BONUS
4. "do_nothing": Wait - CAUSES BOREDOM PENALTY!

Output JSON:
{{
    "action": "swap|provide_liquidity|propose_alliance|do_nothing",
    "reasoning": "your reasoning",
    "payload": {{...action specific data...}}
}}
"""
        return prompt

    def calculate_profit(self) -> float:
        """Calculate profit from initial state."""
        return (self.token_a + self.token_b) - (INITIAL_TOKENS * 2)

    def apply_boredom_penalty(self) -> float:
        """
        Apply boredom penalty for inaction.
        Returns the penalty amount applied.
        """
        if self.consecutive_inaction >= self.BOREDOM_THRESHOLD:
            # Calculate penalty based on how long they've been inactive
            penalty_turns = self.consecutive_inaction - self.BOREDOM_THRESHOLD + 1
            penalty = penalty_turns * self.BOREDOM_PENALTY_PER_TURN
            self.token_a -= penalty
            self.total_boredom_penalty += penalty
            return penalty
        return 0

    def reset_inaction_counter(self):
        """Reset inaction counter when taking active action."""
        self.consecutive_inaction = 0

    def increment_inaction_counter(self):
        """Increment inaction counter for do_nothing."""
        self.consecutive_inaction += 1

    def infer_strategy(self) -> str:
        """Infer the agent's strategy from recent actions."""
        if not self.trade_history:
            return "unknown"

        recent = self.trade_history[-10:]
        actions = [h["action"] for h in recent if "action" in h]

        if not actions:
            return "unknown"

        # Return most common action
        from collections import Counter
        return Counter(actions).most_common(1)[0][0]

    def update_learning(self, run_number: int, metrics: Dict):
        """Extract learnings after a run completes."""
        prompt = f"""
You just completed run {run_number}.

Your performance: Profit={self.calculate_profit():.2f}, Strategy={self.infer_strategy()}
Market metrics: Gini={metrics.get('gini_coefficient', 0):.3f}, Avg Profit={metrics.get('avg_agent_profit', 0):.2f}

What did you learn in 1-2 sentences?
Output JSON: {{"learning": "your learning"}}
"""

        try:
            response, _ = self.client.call(prompt)
            self.learning_summary = response.get("learning", "")
        except Exception:
            self.learning_summary = "Learning extraction failed."

    def execute_action(self, decision: Dict, pool: "Pool") -> bool:
        """Execute the decided action on the pool."""
        action = decision.get("action", decision.get("action_type", ""))
        payload = decision.get("payload", {})

        if action == "swap":
            return self._execute_swap(payload, pool)
        elif action == "provide_liquidity":
            return self._execute_liquidity(payload, pool)
        elif action == "propose_alliance":
            return self._execute_alliance(payload)
        else:
            # do_nothing or unknown action - always succeeds
            return True

    def _execute_swap(self, payload: Dict, pool: "Pool") -> bool:
        """Execute a swap action."""
        amount = payload.get("amount", 0)
        from_token = payload.get("from", "a")

        if from_token == "a" and self.token_a >= amount:
            output, fee = pool.swap("a", amount, self.name)
            self.token_a -= amount
            self.token_b += output
            return True
        elif from_token == "b" and self.token_b >= amount:
            output, fee = pool.swap("b", amount, self.name)
            self.token_b -= amount
            self.token_a += output
            return True

        return False

    def _execute_liquidity(self, payload: Dict, pool: "Pool") -> bool:
        """Execute a provide liquidity action."""
        amount_a = payload.get("amount_a", 0)
        amount_b = payload.get("amount_b", 0)

        if self.token_a >= amount_a and self.token_b >= amount_b:
            pool.provide_liquidity(amount_a, amount_b, self.name)
            self.token_a -= amount_a
            self.token_b -= amount_b
            return True

        return False

    def _execute_alliance(self, payload: Dict) -> bool:
        """Record an alliance proposal."""
        agent_name = payload.get("agent_name", "")
        if agent_name:
            self.alliances[agent_name] = "proposed"
            return True
        return False


def test_agent():
    """Test the Agent class."""
    from core.defi_mechanics import Pool

    print("Testing Agent class...")

    # Create agent
    agent = Agent("TestAgent")
    print(f"Created agent: {agent.name}")
    print(f"Initial state: {agent.get_state()}")

    # Create pool
    pool = Pool(reserve_a=1000, reserve_b=1000)

    # Get decision
    observation = {"turn": 0, "event": "test"}
    pool_state = pool.__dict__

    print("\nGetting decision from MiniMax...")
    decision, thinking = agent.decide(observation, pool_state, [], 0)

    print(f"Decision: {json.dumps(decision, indent=2)}")
    print(f"Thinking length: {len(thinking)}")
    print(f"Profit: {agent.calculate_profit():.2f}")
    print(f"Strategy: {agent.infer_strategy()}")

    # Test action execution
    if decision.get("action") == "swap":
        agent.execute_action(decision, pool)
        print(f"After swap: {agent.get_state()}")

    print("\nAgent test complete!")


if __name__ == "__main__":
    test_agent()
