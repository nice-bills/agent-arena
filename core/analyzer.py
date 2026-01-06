"""Analysis tools for DeFi agent simulation metrics."""

from typing import List, Dict, Optional
from collections import Counter
import statistics


class Analyzer:
    """Calculate and analyze simulation metrics."""

    @staticmethod
    def calculate_run_metrics(agents: List, pool) -> Dict:
        """Calculate all metrics for a completed run."""
        profits = [a.calculate_profit() for a in agents]

        return {
            "gini_coefficient": Analyzer.gini_coefficient(profits),
            "avg_agent_profit": statistics.mean(profits) if profits else 0,
            "min_profit": min(profits) if profits else 0,
            "max_profit": max(profits) if profits else 0,
            "total_trades": Analyzer.count_trades(agents),
            "cooperation_rate": Analyzer.cooperation_rate(agents),
            "pool_stability": pool.reserve_a * pool.reserve_b,
            "pool_price_change": Analyzer.price_change(pool)
        }

    @staticmethod
    def gini_coefficient(values: List[float]) -> float:
        """Calculate Gini coefficient (wealth inequality 0-1)."""
        if not values or sum(values) == 0:
            return 0

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        cumsum = sum((i + 1) * val for i, val in enumerate(sorted_vals))

        gini = (2 * cumsum) / (n * sum(sorted_vals)) - (n + 1) / n
        return max(0, min(1, gini))  # Clamp to 0-1

    @staticmethod
    def count_trades(agents: List) -> int:
        """Count total trades across all agents."""
        return sum(
            len([h for h in a.trade_history if h.get("action") == "swap"])
            for a in agents
        )

    @staticmethod
    def cooperation_rate(agents: List) -> float:
        """Calculate cooperation rate (alliances per agent)."""
        total_alliances = sum(len(a.alliances) for a in agents)
        return total_alliances / max(len(agents), 1)

    @staticmethod
    def price_change(pool) -> float:
        """Calculate pool price change from initial (placeholder)."""
        return 0  # Would need to track initial price

    @staticmethod
    def detect_arms_races(actions: List[Dict]) -> Dict:
        """Detect strategic arms race patterns across agents."""
        strategies = {}
        for action in actions:
            agent = action.get("agent_name", "unknown")
            action_type = action.get("action_type", action.get("action", "unknown"))

            if agent not in strategies:
                strategies[agent] = []
            strategies[agent].append(action_type)

        analysis = {}
        for agent, actions_list in strategies.items():
            if not actions_list:
                continue

            counter = Counter(actions_list)
            most_common = counter.most_common(1)[0]

            analysis[agent] = {
                "dominant_strategy": most_common[0],
                "strategy_counts": dict(counter),
                "strategy_diversity": len(set(actions_list)) / len(actions_list),
                "aggressiveness": Analyzer._calculate_aggressiveness(actions_list)
            }

        return analysis

    @staticmethod
    def _calculate_aggressiveness(actions: List[str]) -> float:
        """Calculate aggressiveness score (0-1)."""
        aggressive_actions = {"swap", "provide_liquidity"}
        passive_actions = {"do_nothing"}

        aggressive_count = sum(1 for a in actions if a in aggressive_actions)
        passive_count = sum(1 for a in actions if a in passive_actions)

        total = len(actions)
        if total == 0:
            return 0.5

        return aggressive_count / total

    @staticmethod
    def detect_trends(runs: List[Dict]) -> Dict:
        """Detect trends across multiple runs."""
        if not runs:
            return {}

        profits = [r.get("avg_agent_profit", 0) for r in runs]
        gini = [r.get("gini_coefficient", 0) for r in runs]

        return {
            "profit_trend": Analyzer._trend_direction(profits),
            "inequality_trend": Analyzer._trend_direction(gini),
            "avg_profit": statistics.mean(profits) if profits else 0,
            "avg_gini": statistics.mean(gini) if gini else 0,
            "run_count": len(runs)
        }

    @staticmethod
    def _trend_direction(values: List[float]) -> str:
        """Get trend direction (up, down, stable)."""
        if len(values) < 2:
            return "stable"

        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])

        diff = second_half - first_half
        if diff > 0.1:
            return "up"
        elif diff < -0.1:
            return "down"
        return "stable"

    @staticmethod
    def format_report(metrics: Dict, agent_count: int = 5) -> str:
        """Format metrics as a readable report."""
        lines = [
            "=" * 40,
            "SIMULATION REPORT",
            "=" * 40,
            f"Agents: {agent_count}",
            "-" * 40,
            f"Gini Coefficient: {metrics.get('gini_coefficient', 0):.4f}",
            f"Avg Profit: {metrics.get('avg_agent_profit', 0):.2f}",
            f"Total Trades: {metrics.get('total_trades', 0)}",
            f"Cooperation Rate: {metrics.get('cooperation_rate', 0):.2f}",
            f"Pool Stability: {metrics.get('pool_stability', 0):.2f}",
            "=" * 40,
        ]

        # Add inequality interpretation
        gini = metrics.get('gini_coefficient', 0)
        if gini < 0.2:
            interpretation = "Low inequality"
        elif gini < 0.4:
            interpretation = "Moderate inequality"
        else:
            interpretation = "High inequality"
        lines.append(f"Inequality: {interpretation}")

        return "\n".join(lines)


def test_analyzer():
    """Test the Analyzer class."""
    print("Testing Analyzer class...")

    # Create mock agents
    class MockAgent:
        def __init__(self, name, profit, alliances, trades):
            self.name = name
            self.profit = profit
            self.alliances = alliances
            self.trade_history = [{"action": t} for t in trades]

        def calculate_profit(self):
            return self.profit

    agents = [
        MockAgent("A", 50, {"B": "ally"}, ["swap", "do_nothing"]),
        MockAgent("B", 30, {"A": "ally"}, ["swap"]),
        MockAgent("C", -20, {}, ["do_nothing", "do_nothing"]),
        MockAgent("D", 40, {}, ["provide_liquidity"]),
        MockAgent("E", 0, {}, ["do_nothing"]),
    ]

    class MockPool:
        reserve_a = 1100
        reserve_b = 909
        price_ab = 0.826

    # Calculate metrics
    metrics = Analyzer.calculate_run_metrics(agents, MockPool())

    print("\nMetrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Format report
    print("\n" + Analyzer.format_report(metrics))

    # Arms race detection
    actions = [
        {"agent_name": "A", "action_type": "swap"},
        {"agent_name": "B", "action_type": "swap"},
        {"agent_name": "A", "action_type": "provide_liquidity"},
    ]
    arms_race = Analyzer.detect_arms_races(actions)
    print("\nArms Race Analysis:")
    for agent, data in arms_race.items():
        print(f"  {agent}: {data}")

    print("\nAnalyzer test complete!")


if __name__ == "__main__":
    test_analyzer()
