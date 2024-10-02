from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import sys

class CodeRunnerThread(QThread):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)

    def __init__(self, code, input_value, debug_mode=False, test_mode=False):
        super().__init__()
        self.code = code
        self.input_value = input_value
        self.debug_mode = debug_mode
        self.test_mode = test_mode

    def run(self):
        try:
            # Construct the command to execute the code
            command = [sys.executable, '-c', self.code]

            # Redirect standard output to capture code output
            output = subprocess.check_output(command, input=self.input_value.encode(), stderr=subprocess.STDOUT)
            self.output_received.emit(output.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            self.error_received.emit(e.output.decode('utf-8'))
