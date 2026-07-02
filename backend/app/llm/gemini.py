"""Groq LLM client wrapper — free tier, fast inference with Llama models."""

import json
import logging
import asyncio
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMClient:
    """Async client for Groq API (OpenAI-compatible interface)."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.LLM_MODEL
        self.client = httpx.AsyncClient(timeout=settings.LLM_TIMEOUT)

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a response from Groq (Llama).

        Args:
            prompt: The user/context prompt
            system_instruction: System-level instruction
            temperature: Sampling temperature
            json_mode: If True, request JSON output format

        Returns:
            The generated text response
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }

        if json_mode:
            body["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self.client.post(
                GROQ_API_URL,
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            return content

        except httpx.HTTPStatusError as e:
            logger.error("Groq API HTTP error %d: %s", e.response.status_code, e.response.text[:200])
            raise
        except Exception as e:
            logger.error("Groq API error: %s", e)
            raise

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> dict:
        """Generate and parse a JSON response."""
        # Add explicit JSON instruction to prompt for reliability
        json_prompt = prompt + "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no extra text."

        response = await self.generate(
            prompt=json_prompt,
            system_instruction=system_instruction,
            json_mode=True,
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            # Try finding JSON object in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            logger.error("Failed to parse JSON from response: %s", response[:200])
            raise ValueError(f"Could not parse JSON from response: {response[:100]}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the singleton LLM client."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
