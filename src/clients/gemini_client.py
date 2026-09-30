import os
from typing import Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str
    model_name: str
    tokens_used: Optional[int] = Field(default=None)


class GeminiAdapter:
    """Adaptador desacoplado para inferencia con modelos Gemini."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY no encontrada en el entorno ni en argumentos.")
        self.client = genai.Client(api_key=key)

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> LLMResponse:
        """Envía un prompt al modelo y retorna un objeto validado LLMResponse."""
        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction

        response = client = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        tokens = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = response.usage_metadata.total_token_count

        return LLMResponse(
            content=response.text or "",
            model_name=self.model_name,
            tokens_used=tokens,
        )
