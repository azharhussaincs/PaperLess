
import unittest
import requests_mock
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from paperless_ai.resolver import OllamaResolver

class TestOllamaResolver(unittest.TestCase):
    def setUp(self):
        # Reset the singleton instance for each test
        OllamaResolver._instance = None
        self.resolver = OllamaResolver()

    @requests_mock.Mocker()
    def test_discovery_fallback_chain(self, m):
        # Mock all endpoints to fail except 127.0.0.1
        m.get("http://host.docker.internal:11434/api/tags", status_code=404)
        m.get("http://localhost:11434/api/tags", status_code=404)
        m.get("http://127.0.0.1:11434/api/tags", status_code=200)

        endpoint = self.resolver.get_endpoint()
        self.assertEqual(endpoint, "http://127.0.0.1:11434")

    @requests_mock.Mocker()
    def test_manual_endpoint_priority(self, m):
        manual = "http://my-ollama:11434"
        # Manual endpoint should be returned immediately without health check (as per current implementation)
        # Actually, looking at the code, it returns manual_endpoint if provided.
        endpoint = self.resolver.get_endpoint(manual_endpoint=manual)
        self.assertEqual(endpoint, manual)

    @requests_mock.Mocker()
    def test_caching(self, m):
        m.get("http://host.docker.internal:11434/api/tags", status_code=200)

        # First call
        self.resolver.get_endpoint()
        self.assertEqual(m.call_count, 1)

        # Second call should use cache
        self.resolver.get_endpoint()
        self.assertEqual(m.call_count, 1)

    @requests_mock.Mocker()
    def test_no_ollama_found(self, m):
        m.get("http://host.docker.internal:11434/api/tags", status_code=404)
        m.get("http://localhost:11434/api/tags", status_code=404)
        m.get("http://127.0.0.1:11434/api/tags", status_code=404)

        endpoint = self.resolver.get_endpoint()
        self.assertIsNone(endpoint)

if __name__ == "__main__":
    unittest.main()
