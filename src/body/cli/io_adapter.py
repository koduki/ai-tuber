"""
入出力管理モジュール。
標準入力からのコメント取得と標準出力への発話を管理します。
"""
from typing import List
from queue import Queue, Empty
import sys
import threading


class IOAdapter:
    """標準入出力を管理し、スレッドセーフなキューでコメントを保持するクラス。"""

    def __init__(self):
        self._input_queue: Queue = Queue()

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


# シングルトンインスタンス
io_adapter = IOAdapter()


def _stdin_reader():
    """標準入力から一行ずつ読み取り、キューに追加するスレッド用の関数。"""
    sys.stderr.write("DEBUG: Starting stdin_reader thread\n")
         
    while True:
        try:
            if hasattr(sys.stdin, 'buffer'):
                line_bytes = sys.stdin.buffer.readline()
                if not line_bytes:
                    break
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


def start_input_reader_thread():
    """非同期に入力を待ち受けるためのスレッドを開始します。"""
    threading.Thread(target=_stdin_reader, daemon=True).start()


# 標準入力のエンコーディング設定
if sys.stdin and hasattr(sys.stdin, 'reconfigure'):
    try:
        sys.stdin.reconfigure(encoding='utf-8')
    except Exception as e:
        sys.stderr.write(f"Warning: Could not reconfigure stdin encoding: {e}\n")
