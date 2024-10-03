#E:\UDH\Compiler\runner\code_runner_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import sys

class CodeRunnerThread(QThread):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)

    def __init__(self, code, input_value):
        super().__init__()
        self.code = code
        self.input_value = input_value

    def run(self):
        try:
            # Construct the command to execute the code
            command = [sys.executable, '-c', self.code]

            # Start the process
            process = subprocess.Popen(command,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            output, error = process.communicate(input=self.input_value.encode())

            # Emit the output if available
            if output:
                self.output_received.emit(output.decode('utf-8'))
            # Emit the error if available
            if error:
                self.error_received.emit(error.decode('utf-8'))
        except Exception as e:
            # Emit any exceptions that occur during the execution
            self.error_received.emit(str(e))
