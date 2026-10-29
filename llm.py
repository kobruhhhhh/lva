"""Ollama answer generation."""

import queue

import ollama

from config import LLM_MODEL, SYSTEM_PROMPT


def generate_answer(transcript: str, ui_queue: queue.Queue) -> None:
    """Stream an answer for a transcript into the UI queue."""
    try:
        stream = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript},
            ],
            stream=True,
        )
        for chunk in stream:
            ui_queue.put(("answer", chunk["message"]["content"]))
    except Exception as error:
        ui_queue.put(("error", f"LLM error (is Ollama running?): {error}"))
    finally:
        ui_queue.put(("answer_done", None))
