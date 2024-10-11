import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication
from core.lint_worker import LintWorker

class TestLintWorker(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        # Initialize a QCoreApplication to handle PyQt signals
        self.app = QCoreApplication([])

    @patch('subprocess.Popen')
    def test_lint_worker_emits_results(self, mock_popen):
        # Mock the subprocess.Popen to simulate flake8 output
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("code.py:1:1: F401 'os' imported but unused\n", "")
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Sample code to lint
        code = "import os\n"

        # Initialize the LintWorker
        worker = LintWorker(code)
        results = []

        # Connect the signal to a slot to capture the results
        worker.lint_result.connect(lambda lint_data: results.extend(lint_data))

        # Run the worker
        worker.run()

        # Check that the results contain the expected lint error
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['line'], 1)
        self.assertEqual(results[0]['message'], "1: F401 'os' imported but unused")

    def tearDown(self):
        """Clean up after tests."""
        self.app.quit()

if __name__ == '__main__':
    unittest.main()
