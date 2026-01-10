from typing import Optional, List
from queue import Queue, Empty
import sys
import asyncio
import threading

# --- I/O Abstraction ---
class IOAdapter:
    def __init__(self):
        self._input_queue = Queue()

    def write_output(self, text: str):
        print(text)

    def add_input(self, text: str):
        self._input_queue.put(text)

    def get_inputs(self) -> List[str]:
        inputs = []
        while not self._input_queue.empty():
            try:
                inputs.append(self._input_queue.get_nowait())
            except Empty:
                break
        return inputs

io_adapter = IOAdapter()

def stdin_reader():
    """Reads lines from stdin and puts them in a queue."""
    sys.stderr.write("DEBUG: Starting stdin_reader thread\n")
    while True:
        try:
            line = sys.stdin.readline()
            if line:
                io_adapter.add_input(line.strip())
        except Exception as e:
            sys.stderr.write(f"Error reading stdin: {e}\n")
            break

# Start stdin reader in background
threading.Thread(target=stdin_reader, daemon=True).start()

# --- Tool Implementations ---

async def speak(text: str, style: Optional[str] = None):
    """Speak the given text with an optional style."""
    style_str = f" ({style})" if style else ""
    io_adapter.write_output(f"\n[AI{style_str}]: {text}")
    return "Speaking completed"

async def change_emotion(emotion: str):
    """Change the visual emotion."""
    io_adapter.write_output(f"\n[Expression]: {emotion}")
    return "Emotion changed"

async def get_comments():
    """Get comments from the adapter."""
    inputs = io_adapter.get_inputs()
    if not inputs:
        return "No new comments."
    return "\n".join(inputs)
