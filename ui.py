"""Tkinter user interface for the local voice assistant."""

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

from audio import AudioCapture
from llm import generate_answer
from transcription import Transcriber


class App:
    """Coordinate the UI, microphone, transcription, and answer workers."""

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Local Voice Assistant")
        root.geometry("720x640")

        self.ui_queue = queue.Queue()
        self.segment_queue = queue.Queue()
        self.audio = AudioCapture(self.segment_queue)
        self.generating = False

        self._build_ui()
        self.audio.start_segmenter()
        Transcriber(self.segment_queue, self.ui_queue).start()
        self.root.after(50, self._drain_ui)

    def _build_ui(self) -> None:
        bar = tk.Frame(self.root)
        bar.pack(fill="x", padx=10, pady=8)

        self.start_btn = tk.Button(
            bar, text="Start", width=10, command=self.start, state="disabled"
        )
        self.stop_btn = tk.Button(
            bar, text="Stop", width=10, command=self.stop, state="disabled"
        )
        self.suggest_btn = tk.Button(
            bar, text="Suggest Answer", width=16, command=self.suggest
        )
        self.clear_btn = tk.Button(
            bar, text="Clear Transcript", width=16, command=self.clear_transcript
        )
        for button in (
            self.start_btn,
            self.stop_btn,
            self.suggest_btn,
            self.clear_btn,
        ):
            button.pack(side="left", padx=(0, 8))

        self.status = tk.Label(bar, text="Loading speech model...", anchor="e")
        self.status.pack(side="right")

        text_area = tk.Frame(self.root)
        text_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        text_area.columnconfigure(0, weight=1)
        text_area.columnconfigure(1, weight=1)
        text_area.rowconfigure(1, weight=1)

        tk.Label(text_area, text="Transcript", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.transcript = scrolledtext.ScrolledText(
            text_area, wrap="word"
        )
        self.transcript.grid(
            row=1, column=0, sticky="nsew", padx=(0, 5)
        )

        tk.Label(text_area, text="AI Answer", anchor="w").grid(
            row=0, column=1, sticky="w", padx=(5, 0)
        )
        self.answer = scrolledtext.ScrolledText(
            text_area, wrap="word"
        )
        self.answer.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

    def _set_status(self, text: str) -> None:
        self.status.config(text=text)

    def _append(self, widget: scrolledtext.ScrolledText, text: str) -> None:
        widget.insert("end", text)
        widget.see("end")

    def _drain_ui(self) -> None:
        """Apply worker updates on the Tk thread."""
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "ready":
                    self.start_btn.config(state="normal")
                    self._set_status("Ready")
                elif kind == "transcript":
                    self._append(self.transcript, payload + " ")
                elif kind == "answer":
                    self._append(self.answer, payload)
                elif kind == "answer_done":
                    self.generating = False
                    self.suggest_btn.config(state="normal")
                    self._set_status("Listening..." if self.audio.stream else "Ready")
                elif kind == "error":
                    self._set_status(payload)
        except queue.Empty:
            pass
        self.root.after(50, self._drain_ui)

    def start(self) -> None:
        try:
            self.audio.start()
        except Exception as error:
            self._set_status(f"Mic error: {error}")
            return
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._set_status("Listening...")

    def stop(self) -> None:
        self.audio.stop()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._set_status("Ready")

    def clear_transcript(self) -> None:
        self.transcript.delete("1.0", "end")

    def suggest(self) -> None:
        text = self.transcript.get("1.0", "end").strip()
        if not text or self.generating:
            return
        self.generating = True
        self.suggest_btn.config(state="disabled")
        self.answer.delete("1.0", "end")
        self._set_status("Generating answer...")
        threading.Thread(
            target=generate_answer,
            args=(text, self.ui_queue),
            daemon=True,
        ).start()
