from typing import Optional, List
from queue import Queue, Empty
import sys
import asyncio
import threading
import urllib.parse
import httpx

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
    if not hasattr(sys.stdin, 'buffer'):
         sys.stderr.write("DEBUG: sys.stdin.buffer not found, using sys.stdin\n")
         
    while True:
        try:
            if hasattr(sys.stdin, 'buffer'):
                line_bytes = sys.stdin.buffer.readline()
                if not line_bytes:
                    break
                # Valid utf-8 is expected, but 'replace' prevents crashing on partial/bad bytes
                line = line_bytes.decode('utf-8', errors='replace')
            else:
                line = sys.stdin.readline()
                if not line:
                    break
            
            if line:
                io_adapter.add_input(line.strip())
        except Exception as e:
            sys.stderr.write(f"Error reading stdin: {e}\n")
            # Don't break on read errors, just log and continue if possible, 
            # though usually an error here means the stream is broken.
            # But let's try to be resilient.
            # actually if readline fails repeatedly we should probably break or sleep to avoid busy loop
            import time
            time.sleep(0.1) 

# Start stdin reader in background
# We don't need to reconfigure encoding if we use buffer, but keeping it harmless.
if sys.stdin and hasattr(sys.stdin, 'reconfigure'):
    try:
        sys.stdin.reconfigure(encoding='utf-8')
    except Exception as e:
        sys.stderr.write(f"Warning: Could not reconfigure stdin encoding: {e}\n")

threading.Thread(target=stdin_reader, daemon=True).start()

# --- Tool Implementations ---

async def speak(text: str, style: Optional[str] = None, **kwargs):
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


