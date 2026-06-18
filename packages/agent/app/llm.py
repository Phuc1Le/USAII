from collections.abc import Iterator
from typing import TypeVar

from fastapi import HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import GEMINI_API_KEY, GEMINI_MODEL


T = TypeVar("T", bound=BaseModel)

_client = genai.Client(api_key=GEMINI_API_KEY)


def json_call(prompt: str, response_schema: type[T]) -> T:
    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, response_schema):
            return parsed
        if parsed is not None:
            return response_schema.model_validate(parsed)

        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini returned an empty JSON response")
        return response_schema.model_validate_json(text)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini JSON call failed: {exc}",
        ) from exc


def stream_text(prompt: str) -> Iterator[str]:
    try:
        stream = _client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini stream failed: {exc}",
        ) from exc
