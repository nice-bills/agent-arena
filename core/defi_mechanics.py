"""DeFi mechanics: Constant product AMM pool."""

from typing import Dict, Tuple
from dataclasses import dataclass, field

from config import SWAP_FEE


@dataclass
class Pool:
    """Constant product automated market maker (AMM)."""

    reserve_a: float = 1000
    reserve_b: float = 1000
    liquidity_providers: Dict[str, float] = field(default_factory=dict)
    _constant_product: float = None

    def __post_init__(self):
        self._constant_product = self.reserve_a * self.reserve_b

    def swap(self, token_in: str, amount_in: float, agent_name: str) -> Tuple[float, float]:
        """
        Execute a swap on the pool.

        Returns:
            Tuple of (amount_out, fee)
        """
        if amount_in <= 0:
            return 0, 0

        if token_in == "a":
            amount_out = self._calculate_output(amount_in, self.reserve_a, self.reserve_b)
            fee = amount_out * SWAP_FEE
            amount_out -= fee

            self.reserve_a += amount_in
            self.reserve_b -= amount_out
        else:
            amount_out = self._calculate_output(amount_in, self.reserve_b, self.reserve_a)
            fee = amount_out * SWAP_FEE
            amount_out -= fee

            self.reserve_b += amount_in
            self.reserve_a -= amount_out

        self._constant_product = self.reserve_a * self.reserve_b
        return amount_out, fee

    def provide_liquidity(self, amount_a: float, amount_b: float, agent_name: str) -> float:
        """Add liquidity to the pool and mint LP tokens."""
        if amount_a <= 0 or amount_b <= 0:
            return 0

        # Calculate LP tokens to mint (simple share model)
        total_liquidity = sum(self.liquidity_providers.values())
        if total_liquidity == 0:
            # Initial liquidity - use geometric mean
            lp_tokens = (amount_a * amount_b) ** 0.5
        else:
            # Proportional to existing liquidity
            share_a = amount_a / self.reserve_a
            share_b = amount_b / self.reserve_b
            share = min(share_a, share_b)  # Use smaller share to prevent imbalance
            lp_tokens = share * (self.reserve_a + self.reserve_b)

        self.reserve_a += amount_a
        self.reserve_b += amount_b
        self.liquidity_providers[agent_name] = (
            self.liquidity_providers.get(agent_name, 0) + lp_tokens
        )

        self._constant_product = self.reserve_a * self.reserve_b
        return lp_tokens

    def withdraw_liquidity(self, lp_tokens: float, agent_name: str) -> Tuple[float, float]:
        """Remove liquidity and burn LP tokens."""
        total_lp = sum(self.liquidity_providers.values())
        if total_lp == 0 or lp_tokens <= 0:
            return 0, 0

        share = lp_tokens / total_lp
        amount_a = self.reserve_a * share
        amount_b = self.reserve_b * share

        self.reserve_a -= amount_a
        self.reserve_b -= amount_b
        self.liquidity_providers[agent_name] -= lp_tokens

        self._constant_product = self.reserve_a * self.reserve_b
        return amount_a, amount_b

    @property
    def price_ab(self) -> float:
        """Get price of A in terms of B."""
        return self.reserve_b / self.reserve_a if self.reserve_a > 0 else 0

    @property
    def price_ba(self) -> float:
        """Get price of B in terms of A."""
        return self.reserve_a / self.reserve_b if self.reserve_b > 0 else 0

    @property
    def total_liquidity(self) -> float:
        """Get total liquidity in the pool."""
        return sum(self.liquidity_providers.values())

    @property
    def constant_product(self) -> float:
        """Get the constant product k = a * b."""
        if self._constant_product is None:
            self._constant_product = self.reserve_a * self.reserve_b
        return self._constant_product

    @staticmethod
    def _calculate_output(amount_in: float, reserve_in: float, reserve_out: float) -> float:
        """
        Calculate output amount using constant product formula.
        (x + dx) * (y - dy) = x * y
        dy = y * dx / (x + dx)
        """
        if amount_in <= 0 or reserve_in <= 0 or reserve_out <= 0:
            return 0

        numerator = amount_in * reserve_out
        denominator = reserve_in + amount_in

        return numerator / denominator

    def get_state(self) -> Dict:
        """Get pool state for agents."""
        return {
            "reserve_a": self.reserve_a,
            "reserve_b": self.reserve_b,
            "price_ab": self.price_ab,
            "price_ba": self.price_ba,
            "total_liquidity": self.total_liquidity,
            "constant_product": self.constant_product
        }


def test_pool():
    """Test the Pool class."""
    print("Testing Pool class...")

    # Create pool
    pool = Pool(reserve_a=1000, reserve_b=1000)
    print(f"Initial pool: A={pool.reserve_a}, B={pool.reserve_b}")
    print(f"Price A/B: {pool.price_ab:.4f}")
    print(f"Constant product: {pool.constant_product}")

    # Test swap
    print("\nTesting swap: 100 A for B...")
    amount_out, fee = pool.swap("a", 100, "TestAgent")
    print(f"Output: {amount_out:.4f} B, Fee: {fee:.4f}")
    print(f"Pool after swap: A={pool.reserve_a:.2f}, B={pool.reserve_b:.2f}")

    # Test liquidity provision
    print("\nTesting liquidity provision...")
    lp = pool.provide_liquidity(200, 200, "TestAgent")
    print(f"LP tokens minted: {lp:.4f}")
    print(f"Total liquidity: {pool.total_liquidity:.4f}")

    print("\nPool test complete!")


if __name__ == "__main__":
    test_pool()
