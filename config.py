"""Configuration for DeFi Agents Simulation."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this config file
config_dir = Path(__file__).parent
load_dotenv(config_dir / ".env")

# MiniMax Configuration
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MODEL_NAME = "MiniMax-M2.1"
REASONING_SPLIT = True

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Simulation Configuration
NUM_AGENTS = int(os.getenv("NUM_AGENTS", "5"))
TURNS_PER_RUN = int(os.getenv("TURNS_PER_RUN", "5"))
TOTAL_RUNS = int(os.getenv("TOTAL_RUNS", "100"))

# Token Configuration
INITIAL_TOKENS = int(os.getenv("INITIAL_TOKENS", "100"))

# Pool Configuration
POOL_RESERVE_A = int(os.getenv("POOL_RESERVE_A", "1000"))
POOL_RESERVE_B = int(os.getenv("POOL_RESERVE_B", "1000"))
SWAP_FEE = float(os.getenv("SWAP_FEE", "0.003"))
