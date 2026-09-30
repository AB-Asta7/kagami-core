import os
import time
from typing import Optional, Any, List
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str
    model_name: str
    tokens_used: Optional[int] = Field(default=None)


class GeminiAdapter:
    """Adaptador con tolerancia a fallos, reintento exponencial y cascada de modelos."""

    DEFAULT_MODELS: List[str] = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY no encontrada en el entorno ni en argumentos.")
        self.client = genai.Client(api_key=key)
        self.models_to_try = [model_name] if model_name else self.DEFAULT_MODELS

    def generate(
        self,
        contents: Any = None,
        prompt: Any = None,
        system_instruction: Optional[str] = None,
        max_retries_per_model: int = 2,
    ) -> LLMResponse:
        payload_content = contents if contents is not None else prompt
        if payload_content is None:
            raise ValueError("Se debe proporcionar 'contents' o 'prompt'.")

        config = types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )
        if system_instruction:
            config.system_instruction = system_instruction

        last_exception = None

        for model in self.models_to_try:
            for attempt in range(1, max_retries_per_model + 1):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=payload_content,
                        config=config,
                    )

                    tokens = None
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        tokens = response.usage_metadata.total_token_count

                    return LLMResponse(
                        content=response.text or "",
                        model_name=model,
                        tokens_used=tokens,
                    )

                except Exception as exc:
                    last_exception = exc
                    err_str = str(exc)
                    # Si es error de saturación o no encontrado, aplicar pausa o saltar de modelo
                    if "503" in err_str or "UNAVAILABLE" in err_str:
                        time.sleep(2.0 * attempt)
                        continue
                    if "404" in err_str or "NOT_FOUND" in err_str:
                        break  # Pasar inmediatamente al siguiente modelo de la lista
                    raise exc

        raise last_exception or RuntimeError("No se pudo completar la inferencia en ningún modelo.")
