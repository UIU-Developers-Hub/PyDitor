import subprocess
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class LintWorker(QThread):
    lint_result = pyqtSignal(list)

    def __init__(self, code):
        super().__init__()
        self.code = code
        self.process = None

    def run(self):
        """Run the linting process and emit results."""
        try:
            lint_output = self._run_flake8()
            lint_data = self._parse_flake8_output(lint_output)
            if lint_data:
                self.lint_result.emit(lint_data)
        except Exception as e:
            logging.error(f"Linting error: {e}")
        finally:
            self._terminate_and_cleanup()

    def _run_flake8(self):
        """Run the Flake8 linter on the provided code using subprocess."""
        try:
            self.process = subprocess.Popen(
                ['flake8', '--stdin-display-name', 'code.py', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, _ = self.process.communicate(input=self.code)
            return output
        except FileNotFoundError as e:
            logging.error(f"Flake8 not found: {e}")
            raise FileNotFoundError("Flake8 is not installed. Please install it to use linting.")
        except Exception as e:
            logging.error(f"An error occurred while running Flake8: {e}")
            raise

    def _parse_flake8_output(self, lint_output):
        """Parse the Flake8 output into a structured list of errors."""
        lint_errors = []
        if lint_output:
            for line in lint_output.splitlines():
                parts = line.split(":")
                if len(parts) >= 3:
                    lint_errors.append({
                        "line": int(parts[1]),  # The line number from Flake8 output
                        "message": parts[2].strip(),  # The error message
                    })
        return lint_errors

    def _terminate_and_cleanup(self):
        """Terminate the subprocess if it's still running and clean up resources."""
        if self.process:
            try:
                if self.process.poll() is None:  # Check if the process is still running
                    self.process.terminate()
                    self.process.wait(3)  # Give the process time to terminate
            except subprocess.TimeoutExpired:
                logging.error("Flake8 process timed out, killing the process.")
                self.process.kill()

    def stop(self):
        """Stop the linting process safely."""
        if self.process and self.process.poll() is None:  # If the process is still running
            self.process.terminate()  # Try to terminate the process gracefully
        self.terminate()  # Terminate the QThread
        self.wait()  # Wait for the thread to finish
