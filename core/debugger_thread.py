# File: core/debugger_thread.py

import sys
import subprocess
import queue
import threading
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DebuggerThread(QThread):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    variable_value = pyqtSignal(str, str)

    def __init__(self, code: str):
        super().__init__()
        self.code = code
        self.command_queue = queue.Queue()
        self.running = True

    def run(self):
        temp_filename = "temp_debug_script.py"
        try:
            # Write code to a temporary file for debugging
            with open(temp_filename, "w") as temp_file:
                temp_file.write(self.code)

            logging.info(f"Starting debugger for code in {temp_filename}")

            # Start pdb in a subprocess
            self.process = subprocess.Popen(
                [sys.executable, "-m", "pdb", temp_filename],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            input_thread = threading.Thread(target=self.process_input)
            input_thread.daemon = True
            input_thread.start()

            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_received.emit(line)

            self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.error_received.emit(str(e))
            logging.error(f"Debugger error: {str(e)}")
        finally:
            if self.process:
                logging.debug(f"Terminating debugger process.")
                self.process.terminate()
            if os.path.exists(temp_filename):
                logging.debug(f"Deleting temp file: {temp_filename}")
                os.remove(temp_filename)

    def process_input(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=1)
                if command and self.process.stdin:
                    logging.debug(f"Sending command to debugger: {command}")
                    self.process.stdin.write(command + "\n")
                    self.process.stdin.flush()
            except queue.Empty:
                continue
            except Exception as e:
                self.error_received.emit(f"Failed to send command: {str(e)}")

    def send_command(self, command: str):
        self.command_queue.put(command)

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                logging.info(f"Terminating debugger process.")
            except Exception as e:
                self.error_received.emit(f"Failed to terminate debugger: {str(e)}")
