# Local Voice Assistant

A local desktop voice assistant that transcribes speech and generates answers
using an LLM. Audio and conversations stay on your machine.

## What is used

- **Python 3.10+**
- **Tkinter** for the desktop interface
- **faster-whisper** for local speech-to-text
- **sounddevice** and **NumPy** for microphone input
- **Ollama** for local LLM responses
- **llama3.2:3b** as the default Ollama model

## Setup

1. Install Python 3.10 or newer.
2. Install [Ollama](https://ollama.com).
3. Download the default LLM:

   ```bash
   ollama pull llama3.2:3b
   ```

4. Start Ollama if it is not already running.
5. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Start the application:

   ```bash
   python app.py
   ```

On the first launch, faster-whisper downloads the speech-to-text model.

## Usage

1. Wait until the status says **Ready**.
2. Click **Start** and speak.
3. Click **Suggest Answer** to generate a response.
4. Click **Clear Transcript** to remove the previous transcript.
5. Click **Stop** to release the microphone.
