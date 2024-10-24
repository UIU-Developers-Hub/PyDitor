import sys
import subprocess
import logging
from PyQt6.QtCore import QThread, pyqtSignal, QObject

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class Signals(QObject):
    """Signals to communicate between threads and the main UI."""
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)


class CodeRunnerThread(QThread):
    def __init__(self, file_path, input_value, signals, timeout=5):
        super().__init__()
        self.file_path = file_path
        self.input_value = input_value
        self.signals = signals
        self.timeout = timeout
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.file_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                output, error = self.process.communicate(input=self.input_value, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                output, error = self.process.communicate()

            if output:
                self.signals.output_received.emit(output)
            if error:
                self.signals.error_received.emit(error)

        except Exception as e:
            self.signals.error_received.emit(f"Exception occurred: {str(e)}")
        finally:
            self._terminate_and_cleanup()

    def _terminate_and_cleanup(self):
        if self.process:
            try:
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait(3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.quit()
        self.wait()
