# File: manual_lint_test.py

import os
import time
from ui.code_editor import LintWorker
from PyQt6.QtCore import QCoreApplication, QEventLoop

# Function to handle the lint results emitted by LintWorker
def handle_lint_results(lint_data):
    if lint_data:
        print("Lint errors found:")
        for error in lint_data:
            print(f"Line {error.get('line', 'N/A')}: {error.get('message', 'No message provided')}")
    else:
        print("No lint errors found.")

# Main function to run the lint test
def run_lint_worker_test():
    # Start a QCoreApplication to manage threading in a PyQt environment
    app = QCoreApplication([])

    # Define some test code that is intentionally invalid
    test_code_invalid = "def invalid_code():\n    print 'Hello'"  # Python 2-style print to trigger linting error
    test_code_valid = "def valid_code():\n    print('Hello, World!')"  # Proper Python 3 syntax

    temp_filename = "temp_code.py"

    # Create the lint worker with invalid code to trigger errors
    lint_worker = LintWorker(test_code_invalid, temp_filename)

    # Connect the lint result signal to the handle_lint_results function
    lint_worker.lint_result.connect(handle_lint_results)

    print("==== LintWorker Test with Invalid Code ====")
    lint_worker.start()

    # Allow time for lint worker to start processing
    time.sleep(3)

    # Manually delete the temp file to simulate a deletion conflict
    try:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            print(f"Manually deleted '{temp_filename}' to test race condition handling.")
    except Exception as e:
        print(f"Manual deletion failed: {e}")

    # Allow time for lint worker to complete
    while lint_worker.isRunning():
        app.processEvents(QEventLoop.AllEvents, 100)

    # Run a test with valid code as well
    print("\n==== LintWorker Test with Valid Code ====")
    lint_worker = LintWorker(test_code_valid, temp_filename)
    lint_worker.lint_result.connect(handle_lint_results)
    lint_worker.start()

    # Allow time for lint worker to complete
    while lint_worker.isRunning():
        app.processEvents(QEventLoop.AllEvents, 100)

    print("\n==== LintWorker Test Complete ====")


# Run the test function
if __name__ == "__main__":
    run_lint_worker_test()
