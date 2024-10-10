#core\code_runner_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os

class CodeRunnerThread(QThread):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)

    def __init__(self, code: str, input_value: str, timeout: int = 10):
        super().__init__()
        self.code = code
        self.input_value = input_value
        self.timeout = timeout

    def run(self):
        temp_filename = "temp_code_runner.py"
        try:
            # Write the code to a temporary file
            with open(temp_filename, "w") as temp_file:
                temp_file.write(self.code)

            # Construct the command to execute the code
            command = [sys.executable, temp_filename]

            # Start the process with a timeout to prevent indefinite hangs
            process = subprocess.Popen(command,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)
            try:
                output, error = process.communicate(input=self.input_value.encode(), timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                self.error_received.emit("Code execution timed out.")
                return

            # Emit the output if available
            if output:
                self.output_received.emit(output)
            if error:
                self.error_received.emit(error)
        except Exception as e:
            self.error_received.emit(f"Exception occurred: {str(e)}")
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)  # Clean up temporary file
