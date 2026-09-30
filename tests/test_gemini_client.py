from unittest.mock import MagicMock, patch
import pytest
from src.clients.gemini_client import GeminiAdapter, LLMResponse


def test_gemini_adapter_missing_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GEMINI_API_KEY no encontrada"):
            GeminiAdapter(api_key=None)


@patch("src.clients.gemini_client.genai.Client")
def test_gemini_adapter_generate_success(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = "Respuesta mockeada"
    mock_response.usage_metadata.total_token_count = 42
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiAdapter(api_key="fake-test-key")
    result = adapter.generate(prompt="Hola mundo")

    assert isinstance(result, LLMResponse)
    assert result.content == "Respuesta mockeada"
    assert result.model_name == "gemini-2.5-flash"
    assert result.tokens_used == 42
