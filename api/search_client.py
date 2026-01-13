"""Search tool for MiniMax M2.1 - uses Brave Search (free tier available)."""

import json
import os
import urllib.request
import urllib.error
from urllib.parse import quote
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
import sys

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from config import MINIMAX_API_KEY


def web_search(query: str, api_key: str | None = None) -> str:
    """Search using Brave Search API (free tier: 2,000 queries/month)."""
    brave_key = api_key or os.environ.get("BRAVE_API_KEY", "")

    if brave_key:
        url = f"https://api.search.brave.com/res/v1/web/search?q={quote(query)}"
        req = urllib.request.Request(
            url,
            headers={"X-Subscription-Token": brave_key, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = []
                for item in data.get("web", {}).get("results", [])[:5]:
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("description", ""),
                        }
                    )
                return json.dumps(results)
        except Exception as e:
            return json.dumps([{"error": str(e)}])

    # Fallback: DuckDuckGo instant answer API (free, no key)
    url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = []
            for item in data.get("RelatedTopics", [])[:5]:
                if isinstance(item, dict) and "Title" in item:
                    results.append(
                        {
                            "title": item.get("Title", ""),
                            "url": item.get("URL", ""),
                            "snippet": item.get("Text", ""),
                        }
                    )
            return json.dumps(results)
    except Exception as e:
        return json.dumps([{"error": str(e)}])


def search_with_minimax(query: str, max_tokens: int = 2048) -> str:
    """Search the web and use MiniMax to summarize."""
    api_key = os.environ.get("MINIMAX_API_KEY", "") or MINIMAX_API_KEY

    if not api_key:
        return "Error: MINIMAX_API_KEY not set"

    # Step 1: Search the web
    search_results = web_search(query)

    # Step 2: Ask MiniMax to summarize
    payload = json.dumps(
        {
            "model": "MiniMax-M2.1",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful coding assistant. Summarize the search results with relevant URLs and code examples.",
                },
                {
                    "role": "user",
                    "content": f"Search query: {query}\n\nResults:\n{search_results}\n\nProvide a concise summary with relevant links.",
                },
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.minimax.io/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    except urllib.error.HTTPError as e:
        return f"HTTP Error: {e.code}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = search_with_minimax(query)
        print(result)
    else:
        print("Usage: python api/search_client.py <query>")
        print("\nOptional: Set BRAVE_API_KEY in .env for better results")
