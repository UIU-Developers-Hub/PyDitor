# File: runner/debugger_thread.py

import sys
import pdb
import threading
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class DebuggerThread(QThread):
    """A thread to manage debugging using Python's pdb module."""
    output_received = pyqtSignal(str)  # Signal emitted when output from the debugger is received
    error_received = pyqtSignal(str)   # Signal emitted when an error occurs
    variable_value = pyqtSignal(str, str)  # Signal to emit the value of a variable

    def __init__(self, code):
        super().__init__()
        self.code = code
        self.command_queue = []  # Queue for storing commands like 'continue', 'step', etc.
        self.queue_lock = threading.Lock()
        self.running = True

    def run(self):
        """Start the debugging session with the given code."""
        # Write the code to a temporary file
        temp_filename = "temp_debug_script.py"
        with open(temp_filename, "w") as temp_file:
            temp_file.write(self.code)

        try:
            # Create a subprocess with Python's pdb debugger
            self.process = subprocess.Popen(
                [sys.executable, "-m", "pdb", temp_filename],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Start a thread to handle input commands
            input_thread = threading.Thread(target=self.process_input)
            input_thread.daemon = True
            input_thread.start()

            # Continuously read output from the process
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_received.emit(line)

            self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.error_received.emit(str(e))

    def process_input(self):
        """Handle sending commands to the debugger process."""
        while self.running:
            with self.queue_lock:
                if self.command_queue:
                    command = self.command_queue.pop(0)
                    if self.process and self.process.stdin:
                        try:
                            self.process.stdin.write(command + "\n")
                            self.process.stdin.flush()
                        except Exception as e:
                            self.error_received.emit(f"Failed to send command: {str(e)}")

    def send_command(self, command):
        """Add a command to the queue to be processed."""
        with self.queue_lock:
            self.command_queue.append(command)

    def evaluate_expression(self, expression):
        """Evaluate an expression in the current debugging context."""
        self.send_command(f"p {expression}")

    def stop(self):
        """Stop the debugging thread."""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
            except Exception as e:
                self.error_received.emit(f"Failed to terminate debugger: {str(e)}")
