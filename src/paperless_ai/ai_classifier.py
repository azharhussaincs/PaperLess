import logging

from django.contrib.auth.models import User

from documents.models import Document
from documents.permissions import get_objects_for_user_owner_aware
from paperless.config import AIConfig
from paperless_ai.client import AIClient
from paperless_ai.indexing import query_similar_documents_from_text
from paperless_ai.indexing import truncate_content

logger = logging.getLogger("paperless_ai.rag_classifier")


def build_prompt_without_rag(text: str, filename: str = "") -> str:
    content = truncate_content(text[:4000] or "")

    return f"""
    You are a document classification assistant.

    Analyze the following document and extract the following information:
    - A short descriptive title
    - Tags that reflect the content
    - Names of people or organizations mentioned
    - The type or category of the document
    - Suggested folder paths for storing the document
    - Up to 3 relevant dates in YYYY-MM-DD format

    Filename:
    {filename}

    Content:
    {content}
    """.strip()


def build_prompt_with_rag(text: str, filename: str = "", document: Document | None = None, user: User | None = None) -> str:
    base_prompt = build_prompt_without_rag(text, filename)
    context = truncate_content(get_context_for_document(text, filename, document, user))

    return f"""{base_prompt}

    Additional context from similar documents:
    {context}
    """.strip()


def get_context_for_document(
    text: str,
    filename: str = "",
    doc: Document | None = None,
    user: User | None = None,
    max_docs: int = 5,
) -> str:
    visible_documents = (
        get_objects_for_user_owner_aware(
            user,
            "view_document",
            Document,
        )
        if user
        else None
    )
    similar_docs = query_similar_documents_from_text(
        text=text,
        filename=filename,
        document_ids=[document.pk for document in visible_documents]
        if visible_documents
        else None,
    )[:max_docs]
    context_blocks = []
    for similar in similar_docs:
        text_content = similar.content[:1000] or ""
        title = similar.title or similar.filename or "Untitled"
        context_blocks.append(f"TITLE: {title}\n{text_content}")
    return "\n\n".join(context_blocks)


def parse_ai_response(raw: dict) -> dict:
    return {
        "title": raw.get("title", ""),
        "tags": raw.get("tags", []),
        "correspondents": raw.get("correspondents", []),
        "document_types": raw.get("document_types", []),
        "storage_paths": raw.get("storage_paths", []),
        "dates": raw.get("dates", []),
    }


def get_ai_document_classification(
    document: Document,
    user: User | None = None,
) -> dict:
    return get_ai_document_classification_from_text(
        text=document.content or "",
        filename=document.filename or "",
        document=document,
        user=user,
    )


def get_ai_document_classification_from_text(
    text: str,
    filename: str = "",
    document: Document | None = None,
    user: User | None = None,
) -> dict:
    ai_config = AIConfig()

    prompt = (
        build_prompt_with_rag(text, filename, document, user)
        if ai_config.llm_embedding_backend
        else build_prompt_without_rag(text, filename)
    )

    client = AIClient()
    result = client.run_llm_query(prompt)
    return parse_ai_response(result)
