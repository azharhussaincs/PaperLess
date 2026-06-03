import logging
from typing import TYPE_CHECKING

from paperless.models import LLMBackend

if TYPE_CHECKING:
    from llama_index.core.llms import ChatMessage
    from llama_index.llms.ollama import Ollama
    from llama_index.llms.openai_like import OpenAILike

from paperless.config import AIConfig
from paperless.network import validate_outbound_http_url
from paperless_ai.base_model import DocumentClassifierSchema

logger = logging.getLogger("paperless_ai.client")


class AIClient:
    """
    A client for interacting with an LLM backend.
    """

    def __init__(self) -> None:
        self.settings = AIConfig()
        self.llm = self.get_llm()

    def get_llm(self) -> "Ollama | OpenAILike":
        backend_timeout = int(getattr(self.settings, "llm_timeout", 120))
        if self.settings.llm_backend == LLMBackend.OLLAMA:
            from llama_index.llms.ollama import Ollama
            from paperless_ai.resolver import get_ollama_endpoint, get_ollama_model

            endpoint = get_ollama_endpoint(self.settings.llm_endpoint)
            if not endpoint:
                raise ValueError(
                    "Ollama not found. Please ensure Ollama is installed and running "
                    "on your host machine. If you are on Linux, check that OLLAMA_HOST is set to 0.0.0.0.",
                )

            validate_outbound_http_url(
                endpoint,
                allow_internal=self.settings.llm_allow_internal_endpoints,
            )

            model_name = get_ollama_model(endpoint, self.settings.llm_model)
            if not model_name:
                logger.warning(
                    "No models found in Ollama at %s. AI features will be limited. "
                    "Try running: ollama pull llama3.1",
                    endpoint,
                )
                # Fallback to a default if nothing is found, so at least it tries
                model_name = self.settings.llm_model or "llama3.1"

            return Ollama(
                model=model_name,
                base_url=endpoint,
                request_timeout=backend_timeout,
            )
        elif self.settings.llm_backend == LLMBackend.OPENAI_LIKE:
            from llama_index.llms.openai_like import OpenAILike

            endpoint = self.settings.llm_endpoint or None
            if endpoint:
                validate_outbound_http_url(
                    endpoint,
                    allow_internal=self.settings.llm_allow_internal_endpoints,
                )
            return OpenAILike(
                model=self.settings.llm_model or "gpt-3.5-turbo",
                api_base=endpoint,
                api_key=self.settings.llm_api_key,
                is_chat_model=True,
                is_function_calling_model=True,
            )
        else:
            raise ValueError(f"Unsupported LLM backend: {self.settings.llm_backend}")

    def run_llm_query(self, prompt: str) -> str:
        logger.debug(
            "Running LLM query against %s with model %s",
            self.settings.llm_backend,
            self.settings.llm_model,
        )

        from llama_index.core.llms import ChatMessage
        from llama_index.core.program.function_program import get_function_tool

        user_msg = ChatMessage(role="user", content=prompt)
        tool = get_function_tool(DocumentClassifierSchema)
        result = self.llm.chat_with_tools(
            tools=[tool],
            user_msg=user_msg,
            chat_history=[],
        )
        tool_calls = self.llm.get_tool_calls_from_response(
            result,
            error_on_no_tool_call=True,
        )
        logger.debug("LLM query result: %s", tool_calls)
        parsed = DocumentClassifierSchema(**tool_calls[0].tool_kwargs)
        return parsed.model_dump()

    def run_chat(self, messages: list["ChatMessage"]) -> str:
        logger.debug(
            "Running chat query against %s with model %s",
            self.settings.llm_backend,
            self.settings.llm_model,
        )
        result = self.llm.chat(messages)
        logger.debug("Chat result: %s", result)
        return result
