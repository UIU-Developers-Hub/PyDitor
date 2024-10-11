# File: core/lint_worker.py

import subprocess
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class LintWorker(QThread):
    lint_result = pyqtSignal(list)

    def __init__(self, code):
        super().__init__()
        self.code = code
        self.process = None  # Track the process

    def run(self):
        try:
            # Run flake8 on the code passed via stdin (in-memory)
            lint_output = self._run_flake8()
            lint_data = self._parse_flake8_output(lint_output)
            if lint_data:
                self.lint_result.emit(lint_data)
        except Exception as e:
            logging.error(f"Linting error: {e}")
        finally:
            self._terminate_and_cleanup()

    def _run_flake8(self):
        """Run flake8 on the code using stdin."""
        self.process = subprocess.Popen(
            ['flake8', '--stdin-display-name', 'code.py', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output, _ = self.process.communicate(input=self.code)
        return output

    def _parse_flake8_output(self, lint_output):
        """Parse the flake8 output."""
        lint_errors = []
        if lint_output:
            for line in lint_output.splitlines():
                parts = line.split(":")
                if len(parts) >= 3:
                    lint_errors.append({
                        "line": int(parts[1]),
                        "message": parts[2].strip(),
                    })
        return lint_errors

    def _terminate_and_cleanup(self):
        """Ensure the process is terminated."""
        if self.process:
            try:
                if self.process.poll() is None:  # Check if the process is still running
                    self.process.terminate()     # Attempt to terminate gracefully
                    self.process.wait(3)         # Wait for it to terminate
            except subprocess.TimeoutExpired:
                self.process.kill()              # Force kill if it takes too long

    def stop(self):
        """Gracefully stop the thread."""
        if self.process and self.process.poll() is None:
            self.process.terminate()  # Try to stop the running process
        self.terminate()  # Stop the thread
        self.wait()  # Wait for the thread to exit
