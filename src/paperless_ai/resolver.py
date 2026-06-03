import logging
import requests
import time
import os
from threading import Lock

logger = logging.getLogger("paperless_ai.resolver")

class OllamaResolver:
    _instance = None
    _lock = Lock()

    # Cache settings
    CACHE_DURATION = 300  # 5 minutes

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OllamaResolver, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.cached_endpoint = None
        self.last_check = 0
        self._initialized = True

    def get_endpoint(self, manual_endpoint=None):
        """
        Returns the best available Ollama endpoint.
        If manual_endpoint is provided, it is prioritized.
        """
        if manual_endpoint:
            return manual_endpoint

        now = time.time()
        if self.cached_endpoint and (now - self.last_check < self.CACHE_DURATION):
            return self.cached_endpoint

        # Discovery chain
        fallbacks = [
            "http://host.docker.internal:11434",
            "http://localhost:11434",
            "http://127.0.0.1:11434",
        ]

        # Add custom endpoint from environment if set but not passed as manual_endpoint
        env_endpoint = os.getenv("PAPERLESS_AI_LLM_ENDPOINT")
        if env_endpoint and env_endpoint not in fallbacks:
            fallbacks.insert(0, env_endpoint)

        for endpoint in fallbacks:
            # First check if it's already running
            if self.health_check(endpoint):
                logger.info(f"Ollama detected and active at {endpoint}")
                self.cached_endpoint = endpoint
                self.last_check = now
                return endpoint

            # If not running, attempt to "trigger" it by waiting (in case it's just starting)
            # or by attempting to reach it with a longer timeout/retry.
            # On some systems, just attempting to connect might wake it up if it's a socket-activated service.
            if self.health_check(endpoint, retry=True):
                logger.info(f"Ollama started and detected at {endpoint}")
                self.cached_endpoint = endpoint
                self.last_check = now
                return endpoint

        logger.debug("No active Ollama instance detected.")
        self.cached_endpoint = None
        self.last_check = now
        return None

    def get_best_model(self, endpoint, preferred_model=None):
        """
        Returns the preferred_model if it exists on the endpoint.
        Otherwise returns the largest available model based on size.
        If no models are installed, returns None.
        """
        if not endpoint:
            return None

        try:
            response = requests.get(f"{endpoint.rstrip('/')}/api/tags", timeout=2)
            if response.status_code == 200:
                models_data = response.json().get('models', [])
                if not models_data:
                    logger.warning(f"Ollama connected at {endpoint} but no models are installed.")
                    return None

                model_names = [m['name'] for m in models_data]

                # 1. Exact match for preferred model
                if preferred_model and preferred_model in model_names:
                    return preferred_model

                # 2. Prefix match for preferred model (e.g. 'llama3' matches 'llama3:latest')
                if preferred_model:
                    for name in model_names:
                        if name.startswith(preferred_model):
                            return name

                # 3. Auto-select the largest model
                # We sort by size (bytes) descending.
                # Larger models are generally smarter (more parameters).
                sorted_models = sorted(models_data, key=lambda x: x.get('size', 0), reverse=True)
                best_model = sorted_models[0]['name']

                logger.info(f"Auto-selected largest model: {best_model} ({sorted_models[0].get('size', 0)} bytes)")
                return best_model
        except Exception as e:
            logger.debug(f"Error fetching models from Ollama: {e}")
            pass

        return None

    def health_check(self, endpoint, retry=False):
        """
        Performs a lightweight health check on the Ollama endpoint.
        If retry is True, it will attempt to wait for Ollama to start.
        """
        max_retries = 5 if retry else 1
        for i in range(max_retries):
            try:
                # We use /api/tags as a lightweight check that confirms Ollama is responsive
                response = requests.get(f"{endpoint.rstrip('/')}/api/tags", timeout=2)
                if response.status_code == 200:
                    return True
            except Exception:
                if i < max_retries - 1:
                    logger.info(f"Waiting for Ollama at {endpoint} (attempt {i+1}/{max_retries})...")
                    time.sleep(2)
        return False

def get_ollama_endpoint(manual_endpoint=None):
    return OllamaResolver().get_endpoint(manual_endpoint)

def get_ollama_model(endpoint, preferred_model=None):
    return OllamaResolver().get_best_model(endpoint, preferred_model)
