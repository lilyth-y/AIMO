"""Vertex Gemini client is constructed once per (project, location, api_key) cache key."""

from unittest.mock import MagicMock, patch


def test_genai_client_constructed_once_per_process(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-proj")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.setenv("GOOGLE_GENAI_API_KEY", "fake-key-for-cache-test")

    from src.pipeline import vertex_inference as vi

    vi.reset_vertex_genai_client_cache()

    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "ok"
    mock_instance.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_instance) as mock_client_cls:
        assert vi.generate_vertex("a") == "ok"
        assert vi.generate_vertex("b") == "ok"
        assert mock_client_cls.call_count == 1

    vi.reset_vertex_genai_client_cache()


def test_cache_invalidates_when_api_key_changes(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-proj")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.setenv("GOOGLE_GENAI_API_KEY", "key-one")

    from src.pipeline import vertex_inference as vi

    vi.reset_vertex_genai_client_cache()
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "x"
    mock_instance.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_instance) as mock_client_cls:
        vi.generate_vertex("1")
        assert mock_client_cls.call_count == 1
        monkeypatch.setenv("GOOGLE_GENAI_API_KEY", "key-two")
        vi.generate_vertex("2")
        assert mock_client_cls.call_count == 2

    vi.reset_vertex_genai_client_cache()
