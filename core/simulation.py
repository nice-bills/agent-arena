"""Main simulation engine for DeFi agent market."""

import json
import random
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

    # Alliance bonus config
    ALLIANCE_BONUS: float = 4.0  # Bonus for successful alliance

    # Action bonuses
    LIQUIDITY_BONUS: float = 8.0  # Bonus for providing liquidity
    SWAP_BONUS: float = 3.0       # Bonus for active trading
    COORDINATED_TRADE_BONUS: float = 5.0  # Bonus for trading with allies
    PROFIT_BONUS: float = 10.0    # Bonus for ending turn with positive profit

    # Market maker config
    ENABLE_MARKET_MAKER: bool = True
    MARKET_MAKER_INTERVAL: int = 3  # Market maker acts every N turns
    MARKET_MAKER_VOLATILITY: float = 0.15  # 15% price shock

    def __post_init__(self):
        self.agents: List[Agent] = []
        self.pool: Optional[Pool] = None
        self.current_run_id: Optional[int] = None
        self.current_run_number: int = 0
        self.market_maker_trades: List[Dict] = []

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

        print(f"\n=== Starting run {self.current_run_number} with {self.turns_per_run} turns ===")
        if self.ENABLE_MARKET_MAKER:
            print("Market Maker: ENABLED (creates volatility every 3 turns)")
        if self.ENABLE_CHAOS_AGENT:
            print("Chaos Agent: ENABLED (random unpredictable moves)")
        print(f"Alliance Bonus: {self.ALLIANCE_BONUS} tokens for successful cooperation")
        print(f"Boredom Penalty: Agents lose tokens after 2+ consecutive do_nothing actions")
        print()

        # Register graceful shutdown handler
        import signal
        def shutdown_handler(signum, frame):
            print(f"\n[SHUTDOWN] Received signal, saving progress...")
            _save_progress(self)
            print(f"[SHUTDOWN] Run marked as incomplete")
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

        def _save_progress(sim):
            """Save current progress as incomplete run."""
            if sim.supabase and sim.current_run_id:
                metrics = sim._calculate_metrics()
                try:
                    sim.supabase.update_run_status(sim.current_run_id, "incomplete")
                    sim.supabase.save_metrics(MetricsData(
                        run_id=sim.current_run_id,
                        gini_coefficient=metrics.get("gini_coefficient", 0),
                        cooperation_rate=metrics.get("cooperation_rate", 0),
                        betrayal_count=metrics.get("betrayal_count", 0),
                        avg_agent_profit=metrics.get("avg_agent_profit", 0),
                        pool_stability=metrics.get("pool_stability", 0)
                    ))
                    # Save current states
                    for turn in range(len(sim.agents[0]._turn_actions) if hasattr(sim.agents[0], '_turn_actions') else 0, -1, -1):
                        sim._save_states(turn)
                        break
                except Exception as e:
                    print(f"[SHUTDOWN] Failed to save progress: {e}")

        for turn in range(self.turns_per_run):
            print(f"\n--- Turn {turn + 1}/{self.turns_per_run} ---")

            # Market maker creates volatility every N turns
            if self.ENABLE_MARKET_MAKER and (turn + 1) % self.MARKET_MAKER_INTERVAL == 0:
                self._market_maker_action(turn)

            # Random price shock event (15% chance each turn)
            if random.random() < 0.15:
                self._trigger_price_shock(turn)

            # Chaos agent creates unpredictable moves
            if self.ENABLE_CHAOS_AGENT:
                self._chaos_agent_action(turn)

            # Each agent makes a decision
            for agent in self.agents:
                decision, thinking = self._agent_decide(agent, turn)
                action_type = decision.get('action', 'unknown')

                # Save profit before action for profit detection
                agent._last_profit = agent.calculate_profit()

                # Execute action
                if decision:
                    success = agent.execute_action(decision, self.pool)

                    # Grant bonuses for successful actions
                    if success and action_type != 'do_nothing':
                        self._grant_action_bonus(agent, action_type, decision, turn)

                    # Track inaction
                    if action_type == 'do_nothing':
                        agent.increment_inaction_counter()
                    else:
                        agent.reset_inaction_counter()

                    print(f"  {agent.name}: {action_type} {'OK' if success else 'FAIL'}")

                # Save action to database
                if self.supabase:
                    self._save_action(agent, turn, decision, thinking)

            # Apply boredom penalties AFTER all agents act
            for agent in self.agents:
                penalty = agent.apply_boredom_penalty()
                if penalty > 0:
                    print(f"  {agent.name}: Boredom penalty -{penalty:.1f} tokens")

            # Check for successful alliances and grant bonuses
            self._process_alliances(turn)

            # Grant profit bonus for agents with positive profit
            self._grant_profit_bonuses(turn)

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
                print(f"Generating summary for run {self.current_run_number}...")
                summarizer = Summarizer(supabase=self.supabase)
                summary = summarizer.summarize_and_save(self.current_run_id)
                print(f"Generated summary for run {self.current_run_number}")
            except Exception as e:
                print(f"Warning: Failed to generate summary - {e}")
                import traceback
                traceback.print_exc()

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

    def _market_maker_action(self, turn: int):
        """
        Market maker creates artificial volatility by making large trades.
        This encourages other agents to react and trade.
        """
        # Decide direction: buy A (pushes price up) or buy B (pushes price down)
        direction = random.choice(['buy_a', 'buy_b'])
        amount = self.pool.reserve_a * self.MARKET_MAKER_VOLATILITY

        if direction == 'buy_a':
            # Buy A with B - increases A reserve, decreases B reserve
            output, fee = self.pool.swap('b', amount, 'MarketMaker')
            print(f"  [MarketMaker]: Swapped {amount:.0f} B for {output:.1f} A (volatility trade)")
        else:
            # Buy B with A - increases B reserve, decreases A reserve
            output, fee = self.pool.swap('a', amount, 'MarketMaker')
            print(f"  [MarketMaker]: Swapped {amount:.0f} A for {output:.1f} B (volatility trade)")

        self.market_maker_trades.append({
            'turn': turn,
            'direction': direction,
            'amount': amount,
            'pool_state': self.pool.get_state()
        })

    def _trigger_price_shock(self, turn: int):
        """
        Random external event that causes a price shock.
        Creates trading opportunities for attentive agents.
        """
        # Random shock between -10% and +10%
        shock_pct = random.uniform(-0.10, 0.10)
        direction = "UP" if shock_pct > 0 else "DOWN"

        # Apply shock by doing a large swap
        amount = self.pool.reserve_a * abs(shock_pct)

        if shock_pct > 0:
            # Price goes up: buy A with B
            output, _ = self.pool.swap('b', amount, 'PriceShock')
            print(f"  [EVENT] Price shock {direction} (+{shock_pct*100:.1f}%): Swap {amount:.0f} B -> {output:.1f} A")
        else:
            # Price goes down: buy B with A
            output, _ = self.pool.swap('a', amount, 'PriceShock')
            print(f"  [EVENT] Price shock {direction} ({shock_pct*100:.1f}%): Swap {amount:.0f} A -> {output:.1f} B")

    def _chaos_agent_action(self, turn: int):
        """
        Chaos agent creates unpredictable market moves.
        Forces other agents to react to unexpected volatility.
        """
        # Random chance to act each turn
        if random.random() > 0.20:
            return  # 20% chance - mostly sits out

        # Random action type: 0=swap, 1=liquidity, 2=massive_swap
        action_type = random.choice(['swap', 'liquidity', 'massive_swap'])

        # Random volatility between 15-40%
        volatility = random.uniform(0.15, 0.40)

        if action_type == 'swap':
            # Random direction swap
            direction = random.choice(['a', 'b'])
            amount = self.pool.reserve_a * volatility
            output, fee = self.pool.swap(direction, amount, 'ChaosAgent')
            print(f"  [ChaosAgent]: Random swap {amount:.0f} -> {output:.1f}")

        elif action_type == 'liquidity':
            # Random liquidity provision
            amount_a = self.pool.reserve_a * volatility
            amount_b = self.pool.reserve_b * volatility
            # Liquidity agent doesn't track, just burns tokens for effect
            self.pool.provide_liquidity(amount_a, amount_b, 'ChaosAgent')
            print(f"  [ChaosAgent]: Random liquidity +{amount_a:.0f}A/+{amount_b:.0f}B")

        else:  # massive_swap
            # Huge random trade that moves price significantly
            direction = random.choice(['a', 'b'])
            amount = self.pool.reserve_a * volatility * 1.5  # Even bigger
            output, fee = self.pool.swap(direction, amount, 'ChaosAgent')
            print(f"  [ChaosAgent]: MASSIVE swap {amount:.0f} -> {output:.1f}!")

    def _process_alliances(self, turn: int):
        """
        Process alliances and grant bonuses for mutual proposals.
        When two agents propose alliance to each other, both get a bonus.
        """
        # Find mutual alliance pairs
        for i, agent_a in enumerate(self.agents):
            for agent_b in self.agents[i + 1:]:
                # Check if both have proposed alliance to each other
                if (agent_b.name in agent_a.alliances and
                    agent_a.name in agent_b.alliances and
                    agent_a.alliances.get(agent_b.name) == 'proposed' and
                    agent_b.alliances.get(agent_a.name) == 'proposed'):

                    # Successful alliance! Grant bonus to both (with fatigue)
                    fatigue_a = agent_a.get_alliance_fatigue(agent_b.name)
                    fatigue_b = agent_b.get_alliance_fatigue(agent_a.name)

                    # Apply fatigue - minimum 0 bonus for repeated proposals
                    bonus_a = self.ALLIANCE_BONUS * fatigue_a
                    bonus_b = self.ALLIANCE_BONUS * fatigue_b

                    # Give bonus in Token A
                    agent_a.token_a += bonus_a
                    agent_b.token_a += bonus_b

                    # Record proposals for fatigue tracking
                    agent_a.record_alliance_proposal(agent_b.name)
                    agent_b.record_alliance_proposal(agent_a.name)

                    # Mark alliances as successful
                    agent_a.alliances[agent_b.name] = 'success'
                    agent_b.alliances[agent_a.name] = 'success'

                    # Print appropriate message
                    if fatigue_a == 0 or fatigue_b == 0:
                        print(f"  [ALLIANCE] {agent_a.name} + {agent_b.name}: No bonus (alliance fatigue)")
                    elif fatigue_a == 0.5 or fatigue_b == 0.5:
                        print(f"  [ALLIANCE] {agent_a.name} + {agent_b.name}: HALF bonus +{bonus_a:.1f}/+{bonus_b:.1f} tokens")
                    else:
                        print(f"  [ALLIANCE] {agent_a.name} + {agent_b.name}: BONUS +{bonus_a:.1f}/+{bonus_b:.1f} tokens")

                    if self.supabase:
                        self.supabase.save_action(ActionData(
                            run_id=self.current_run_id,
                            turn=turn,
                            agent_name=f"{agent_a.name}+{agent_b.name}",
                            action_type="alliance_success",
                            payload={"bonus": bonus, "partners": [agent_a.name, agent_b.name]},
                            reasoning_trace=f"Alliance formed between {agent_a.name} and {agent_b.name}",
                            thinking_trace=""
                        ))

    def _grant_action_bonus(self, agent: Agent, action_type: str, decision: Dict, turn: int):
        """
        Grant bonuses for active trading behaviors.

        - Provide liquidity: +8 tokens
        - Swap: +3 tokens (active trading)
        - Coordinated trade with ally: +5 bonus tokens
        - Profitable trade: +5 bonus tokens
        """
        bonus = 0
        bonus_reason = ""

        if action_type == "provide_liquidity":
            bonus = self.LIQUIDITY_BONUS
            bonus_reason = "liquidity provision"

        elif action_type == "swap":
            bonus = self.SWAP_BONUS
            bonus_reason = "active trading"

            # Check for coordinated trade with ally
            if self._is_coordinated_trade(agent, turn):
                bonus += self.COORDINATED_TRADE_BONUS
                bonus_reason = "coordinated trading with ally"

            # Check if swap was profitable (compare pre/post profit)
            if hasattr(agent, '_last_profit'):
                current_profit = agent.calculate_profit()
                if current_profit > agent._last_profit:
                    bonus += 5.0
                    bonus_reason = "profitable trade"

        if bonus > 0:
            agent.token_a += bonus
            print(f"  [BONUS] {agent.name}: +{bonus:.1f} tokens for {bonus_reason}")

            if self.supabase:
                self.supabase.save_action(ActionData(
                    run_id=self.current_run_id,
                    turn=turn,
                    agent_name=agent.name,
                    action_type=f"{action_type}_bonus",
                    payload={"bonus": bonus, "reason": bonus_reason},
                    reasoning_trace=f"Bonus for {bonus_reason}",
                    thinking_trace=""
                ))

    def _is_coordinated_trade(self, agent: Agent, turn: int) -> bool:
        """
        Check if this turn has conditions for coordinated trading.
        Returns True if market volatility events just occurred.
        """
        # Coordinated trades are more valuable after market maker or price shock
        market_maker_just_acted = (turn + 1) % self.MARKET_MAKER_INTERVAL == 0
        price_shock_just_happened = any(
            t.get('turn') == turn for t in getattr(self, 'price_shocks', [])
        ) if hasattr(self, 'price_shocks') else False

        return market_maker_just_acted or price_shock_just_happened

    def _grant_profit_bonuses(self, turn: int):
        """
        Grant bonus tokens to agents with positive profit at end of turn.
        Encourages profit-seeking behavior.
        """
        for agent in self.agents:
            profit = agent.calculate_profit()
            if profit > 0:
                agent.token_a += self.PROFIT_BONUS
                print(f"  [PROFIT BONUS] {agent.name}: +{self.PROFIT_BONUS:.1f} tokens (profit: {profit:.2f})")

                if self.supabase:
                    self.supabase.save_action(ActionData(
                        run_id=self.current_run_id,
                        turn=turn,
                        agent_name=agent.name,
                        action_type="profit_bonus",
                        payload={"bonus": self.PROFIT_BONUS, "profit": profit},
                        reasoning_trace=f"Bonus for positive profit",
                        thinking_trace=""
                    ))


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
