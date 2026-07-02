"""Google Gemini LLM client wrapper with async support."""

import json
import logging
import asyncio
from typing import Optional

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Async wrapper around Google Gemini 2.0 Flash."""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            "gemini-2.0-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: The full prompt including conversation context
            system_instruction: System-level instruction
            temperature: Sampling temperature (lower = more deterministic)
            json_mode: If True, request JSON output format

        Returns:
            The generated text response
        """
        try:
            # Build the model with system instruction if provided
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048,
            )

            if json_mode:
                generation_config.response_mime_type = "application/json"

            model = genai.GenerativeModel(
                "gemini-2.0-flash",
                generation_config=generation_config,
                system_instruction=system_instruction,
            )

            # Run synchronous API call in thread pool to not block event loop
            response = await asyncio.to_thread(
                model.generate_content, prompt
            )

            if response.text:
                return response.text.strip()
            else:
                logger.warning("Gemini returned empty response")
                return ""

        except Exception as e:
            logger.error("Gemini API error: %s", e)
            raise

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> dict:
        """Generate and parse a JSON response from Gemini."""
        response = await self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=True,
        )

        try:
            # Try parsing directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                logger.error("Failed to parse JSON from Gemini response: %s", response[:200])
                raise ValueError(f"Could not parse JSON from response: {response[:100]}")


# Singleton instance
_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the singleton Gemini client."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
