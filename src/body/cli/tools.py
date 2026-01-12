from typing import Optional, List
from queue import Queue, Empty
import sys
import asyncio
import threading

# --- 入出力アダプター ---
class IOAdapter:
    """標準入出力を管理し、スレッドセーフなキューでコメントを保持するクラス。"""
    def __init__(self):
        self._input_queue = Queue()

    def write_output(self, text: str):
        """標準出力にテキストを書き込みます。"""
        print(text)

    def add_input(self, text: str):
        """入力をキューに追加します。"""
        self._input_queue.put(text)

    def get_inputs(self) -> List[str]:
        """キューに溜まっている全ての入力を取得します。"""
        inputs = []
        while not self._input_queue.empty():
            try:
                inputs.append(self._input_queue.get_nowait())
            except Empty:
                break
        return inputs

io_adapter = IOAdapter()

def stdin_reader():
    """標準入力から一行ずつ読み取り、キューに追加するスレッド用の関数。"""
    sys.stderr.write("DEBUG: Starting stdin_reader thread\n")
         
    while True:
        try:
            # バッファ経由で読み取ることでエンコーディングの問題を回避
            if hasattr(sys.stdin, 'buffer'):
                line_bytes = sys.stdin.buffer.readline()
                if not line_bytes:
                    break
                # 不正なバイトが含まれていてもreplaceで回避
                line = line_bytes.decode('utf-8', errors='replace')
            else:
                line = sys.stdin.readline()
                if not line:
                    break
            
            if line:
                io_adapter.add_input(line.strip())
        except Exception as e:
            sys.stderr.write(f"Error reading stdin: {e}\n")
            import time
            time.sleep(0.1) 

# 標準入力のエンコーディング設定
if sys.stdin and hasattr(sys.stdin, 'reconfigure'):
    try:
        sys.stdin.reconfigure(encoding='utf-8')
    except Exception as e:
        sys.stderr.write(f"Warning: Could not reconfigure stdin encoding: {e}\n")

def start_input_reader_thread():
    """非同期に入力を待ち受けるためのスレッドを開始します。"""
    threading.Thread(target=stdin_reader, daemon=True).start()

# --- ツール実装 ---

async def speak(text: str, style: Optional[str] = None, **kwargs):
    """
    指定されたテキストを標準出力に表示（発話）します。
    """
    style_str = f" ({style})" if style else ""
    # [AI (emotion)]: Text の形式で出力
    io_adapter.write_output(f"\n[AI{style_str}]: {text}")
    return "Speaking completed"

async def change_emotion(emotion: str) -> str:
    """
    アバターの感情を変更します。
    （注：現在はログ出力のみですが、将来的にLive2D等の制御を想定しています）
    """
    return f"Emotion changed to {emotion}"

async def get_comments():
    """
    キューに蓄積されたユーザーコメントを取得します。
    """
    inputs = io_adapter.get_inputs()
    if not inputs:
        return "No new comments."
    return "\n".join(inputs)
