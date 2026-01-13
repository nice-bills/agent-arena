"""MiniMax API client with reasoning extraction support - OpenAI compatible."""

import json
from typing import Dict, Tuple, Optional
from openai import OpenAI

from config import MINIMAX_API_KEY, MODEL_NAME, REASONING_SPLIT


class MiniMaxClient:
    """Client for interacting with MiniMax API with reasoning transparency."""

    def __init__(self, api_key: str = None, model: str = None, reasoning_split: bool = None):
        self.api_key = api_key or MINIMAX_API_KEY
        self.model = model or MODEL_NAME
        self.reasoning_split = reasoning_split if reasoning_split is not None else REASONING_SPLIT
        self.base_url = "https://api.minimax.io/v1"

        if not self.api_key:
            raise ValueError("MiniMax API key is required. Set MINIMAX_API_KEY in .env")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def call(self, prompt: str, system_prompt: str = None) -> Tuple[Dict, str]:
        """
        Call MiniMax API with reasoning extraction.

        Returns:
            Tuple of (decision_dict, thinking_text)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                extra_body={"reasoning_split": self.reasoning_split}
            )
        except Exception as e:
            raise RuntimeError(f"MiniMax API call failed: {str(e)}")

        # Extract thinking from reasoning_details
        thinking_text = self._extract_thinking(response)

        # Extract final answer
        content = response.choices[0].message.content
        decision = self._parse_content(content)

        return decision, thinking_text

    def _extract_thinking(self, response) -> str:
        """Extract thinking text from reasoning_details field."""
        try:
            reasoning_details = response.choices[0].message.reasoning_details
            if reasoning_details:
                return reasoning_details[0].text
        except AttributeError:
            pass
        return ""

    def _parse_content(self, content: str) -> Dict:
        """Parse the content into a dictionary."""
        # Try to extract JSON from code block
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_content": content}


def test_client():
    """Test the MiniMax client with a simple query."""
    client = MiniMaxClient()

    prompt = """
    Solve this step by step:
    I have 3 apples. I eat one. A magic bird gives me 2 more apples.
    Then half of my total apples turn into gold.

    How many edible apples do I have left?

    Output JSON:
    {
        "reasoning": "step-by-step thinking",
        "answer": "final answer"
    }
    """

    decision, thinking = client.call(prompt)

    print("=== DECISION ===")
    print(json.dumps(decision, indent=2))
    print("\n=== THINKING ===")
    print(thinking[:500] + "..." if len(thinking) > 500 else thinking)


if __name__ == "__main__":
    test_client()
