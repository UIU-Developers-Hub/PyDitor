# File: core/lint_worker.py

import tempfile
import subprocess
import os
import time
from PyQt6.QtCore import QThread, pyqtSignal
import json

class LintWorker(QThread):
    lint_result = pyqtSignal(list)

    def __init__(self, code):
        super().__init__()
        self.code = code

    def run(self):
        # Create and write code to a temporary file using NamedTemporaryFile
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
            self.temp_filename = temp_file.name
            temp_file.write(self.code.encode())

        try:
            lint_output = self._run_pylint(self.temp_filename)
            lint_data = self._parse_lint_output(lint_output)

            if lint_data:
                self.lint_result.emit(lint_data)
        except Exception as e:
            print(f"Linting error: {e}")
        finally:
            self._safe_delete_temp_file()

    def _run_pylint(self, temp_filename):
        """Run pylint on the temporary file."""
        result = subprocess.run(['pylint', temp_filename, '--output-format', 'json'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')

    def _parse_lint_output(self, lint_output):
        """Parse the JSON output from pylint."""
        if lint_output:
            return json.loads(lint_output)
        return []

    def _safe_delete_temp_file(self):
        """Attempt to delete the temporary file multiple times."""
        retries = 3
        for attempt in range(retries):
            try:
                if os.path.exists(self.temp_filename):
                    os.remove(self.temp_filename)
                    print(f"Successfully deleted temporary file: {self.temp_filename}")
                    return
            except PermissionError:
                print(f"Retrying to delete temporary file: {self.temp_filename}")
                time.sleep(0.5)  # Wait before retrying
        print(f"Failed to delete temporary file '{self.temp_filename}' after {retries} attempts.")
