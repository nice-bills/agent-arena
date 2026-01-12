# DeFi Agents Backend - Docker with uv
FROM python:3.11-slim

WORKDIR /app

# Install uv (fast Python package manager)
ENV UV_SYSTEM=1
ENV UV_COMPILE_BYTECODE=1

# Hugging Face uses port 7860
ENV PORT=7860

# Install Node for frontend build
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Copy only requirements first (for better caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

# Build frontend
WORKDIR /app/frontend
RUN npm install && npm run build
WORKDIR /app

# Expose Hugging Face port
EXPOSE 7860

# Run the FastAPI server with uvicorn
CMD ["uv", "run", "python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "7860"]
