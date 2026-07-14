import subprocess
import threading
import queue
import time
from typing import Optional, Callable, List


class SIMHController:
    """Manages a SIMH emulator as a child process.

    * Reads stdout in a background daemon thread and pushes lines into a
      queue.  An optional *output_callback* is invoked for every line
      (from the reader thread — callers must handle thread safety).
    * Sends commands via stdin.
    * Graceful stop: sends ``exit`` command, waits, then terminates.
    """

    def __init__(self, executable_path: str, startup_options: List[str] | None = None):
        self.executable_path = executable_path
        self.startup_options = startup_options or []
        self.process: Optional[subprocess.Popen] = None
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.running = False
        self.output_callback: Optional[Callable[[str], None]] = None
        self._reader_thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        if self.running:
            return True
        try:
            cmd = [self.executable_path] + self.startup_options
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.running = True
            self._start_reader()
            return True
        except Exception as e:
            print(f"[SIMHController] start error: {e}")
            self.running = False
            return False

    def _start_reader(self):
        def _read():
            while self.running and self.process and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    self.output_queue.put(line)
                    if self.output_callback:
                        self.output_callback(line)
                except Exception:
                    break
            self.running = False

        self._reader_thread = threading.Thread(target=_read, daemon=True)
        self._reader_thread.start()

    def send_command(self, command: str) -> bool:
        if not self.process or not self.running:
            return False
        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            return True
        except Exception:
            return False

    def stop(self):
        if not self.process:
            self.running = False
            return
        try:
            if self.process.poll() is None:
                self.process.stdin.write("exit\n")
                self.process.stdin.flush()
                self.process.wait(timeout=2)
        except Exception:
            pass
        try:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=2)
        except Exception:
            pass
        try:
            if self.process.poll() is None:
                self.process.kill()
        except Exception:
            pass
        self.process = None
        self.running = False

    def is_alive(self) -> bool:
        return self.running and self.process is not None and self.process.poll() is None

    def set_output_callback(self, callback: Callable[[str], None]):
        self.output_callback = callback
