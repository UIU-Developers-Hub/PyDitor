# File: core/code_runner_thread.py

import sys
import subprocess
import logging
from PyQt6.QtCore import QThread, pyqtSignal, QObject

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class Signals(QObject):
    """Signals to communicate between threads and the main UI."""
    output_received = pyqtSignal(str)  # Signal for capturing the standard output
    error_received = pyqtSignal(str)   # Signal for capturing errors


class CodeRunnerThread(QThread):
    def __init__(self, file_path, input_value, signals, timeout=5):
        super().__init__()
        self.file_path = file_path  # Path to the file to run
        self.input_value = input_value  # Any input to be passed to the script
        self.signals = signals  # Signals for communicating output and errors
        self.timeout = timeout  # Timeout for running the process
        self.process = None

    def run(self):
        try:
            # Run the saved file directly using its path
            self.process = subprocess.Popen(
                [sys.executable, self.file_path],  # Command to run the Python file
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # Ensure output is captured as strings
            )

            # Capture the output and errors with a timeout
            try:
                output, error = self.process.communicate(input=self.input_value, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()  # Kill the process if it exceeds the timeout
                output, error = self.process.communicate()  # Capture output/error after force kill

            # Emit the output and error signals
            if output:
                self.signals.output_received.emit(output)
            if error:
                self.signals.error_received.emit(error)

        except Exception as e:
            self.signals.error_received.emit(f"Exception occurred: {str(e)}")
        finally:
            self._terminate_and_cleanup()

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
        self.terminate()
        self.wait()
