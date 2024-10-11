import subprocess
from PyQt6.QtCore import QThread, pyqtSignal
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class LintWorker(QThread):
    lint_result = pyqtSignal(list)

    def __init__(self, code):
        super().__init__()
        self.code = code

    def run(self):
        try:
            # Run flake8 on the code passed via stdin (in-memory)
            lint_output = self._run_flake8()
            lint_data = self._parse_flake8_output(lint_output)
            if lint_data:
                self.lint_result.emit(lint_data)
        except Exception as e:
            logging.error(f"Linting error: {e}")

    def _run_flake8(self):
        """Run flake8 on the code using stdin."""
        result = subprocess.run(
            ['flake8', '--stdin-display-name', 'code.py', '-'],
            input=self.code.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.decode('utf-8')

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
