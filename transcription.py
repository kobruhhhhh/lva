"""Offline speech-to-text worker."""

import queue

from faster_whisper import WhisperModel

from config import WHISPER_MODEL


class Transcriber:
    """Load Whisper and publish transcript messages to the UI queue."""

    def __init__(self, segment_queue: queue.Queue, ui_queue: queue.Queue):
        self.segment_queue = segment_queue
        self.ui_queue = ui_queue

    def run(self) -> None:
        try:
            model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        except Exception as error:
            self.ui_queue.put(("error", f"Failed to load Whisper: {error}"))
            return

        self.ui_queue.put(("ready", None))
        while True:
            audio = self.segment_queue.get()
            segments, _ = model.transcribe(
                audio,
                language="en",
                beam_size=1,
                vad_filter=True,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if text:
                self.ui_queue.put(("transcript", text))

    def start(self):
        import threading

        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread
