"""Microphone capture and energy-based speech segmentation."""

from collections import deque
import queue
import threading

import numpy as np
import sounddevice as sd

from config import (
    AUDIO_BLOCK_SIZE,
    END_SILENCE_BLOCKS,
    MAX_SEGMENT_BLOCKS,
    MIN_SPEECH_BLOCKS,
    SAMPLE_RATE,
    SILENCE_RMS,
)


class AudioCapture:
    """Capture microphone blocks and turn them into speech segments."""

    def __init__(self, segment_queue: queue.Queue):
        self.audio_queue = queue.Queue()
        self.segment_queue = segment_queue
        self.stream = None

    def start(self) -> None:
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=AUDIO_BLOCK_SIZE,
            callback=self._on_audio,
        )
        self.stream.start()

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.audio_queue.put(None)

    def _on_audio(self, indata, frames, time_info, status) -> None:
        self.audio_queue.put(indata[:, 0].copy())

    def run_segmenter(self) -> None:
        """Run the segmenter until the application process exits."""
        pre_roll = deque(maxlen=2)
        buffer = []
        silence_blocks = 0
        speech_blocks = 0

        def emit() -> None:
            nonlocal buffer, silence_blocks, speech_blocks
            if speech_blocks >= MIN_SPEECH_BLOCKS:
                self.segment_queue.put(np.concatenate(buffer))
            buffer, silence_blocks, speech_blocks = [], 0, 0

        while True:
            block = self.audio_queue.get()
            if block is None:
                emit()
                continue

            is_loud = float(np.sqrt(np.mean(block ** 2))) > SILENCE_RMS
            if is_loud:
                if not buffer:
                    buffer.extend(pre_roll)
                buffer.append(block)
                speech_blocks += 1
                silence_blocks = 0
            elif buffer:
                buffer.append(block)
                silence_blocks += 1
                if silence_blocks >= END_SILENCE_BLOCKS:
                    emit()
            pre_roll.append(block)

            if len(buffer) >= MAX_SEGMENT_BLOCKS:
                emit()

    def start_segmenter(self) -> threading.Thread:
        thread = threading.Thread(target=self.run_segmenter, daemon=True)
        thread.start()
        return thread
