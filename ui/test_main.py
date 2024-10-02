import unittest
from PyQt6.QtWidgets import QApplication
from ui.main_window import AICompilerMainWindow  # Adjust the import based on your project structure

class TestAICompilerMainWindow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])  # Create a QApplication instance
        cls.main_window = AICompilerMainWindow()  # Initialize the main window

    def test_documentation_fetching(self):
        """Test that fetching documentation works correctly."""
        self.main_window.documentation_sidebar.show()  # Show the documentation sidebar
        current_widget = self.main_window.tab_widget.currentWidget()
        current_widget.fetch_documentation("def")
        content = self.main_window.documentation_sidebar.widget().toPlainText()
        self.assertIn("Defines a function in Python.", content)  # Check the documentation content

    def test_code_execution(self):
        """Test that valid code runs and produces output."""
        code = "print('Hello, World!')"
        current_widget = self.main_window.tab_widget.currentWidget()
        current_widget.setPlainText(code)  # Set code in the editor
        self.main_window.run_code()  # Run the code
        output = self.main_window.output_text.toPlainText()
        self.assertIn("Hello, World!", output)  # Check that the output is correct

    def test_invalid_code_execution(self):
        """Test that invalid code raises an error."""
        code = "print('Hello, World!'"  # Missing closing parenthesis
        current_widget = self.main_window.tab_widget.currentWidget()
        current_widget.setPlainText(code)  # Set invalid code in the editor
        self.main_window.run_code()  # Run the code
        error_output = self.main_window.output_text.toPlainText()
        self.assertIn("SyntaxError", error_output)  # Check for syntax error in output

    @classmethod
    def tearDownClass(cls):
        cls.main_window.close()  # Close the main window
        cls.app.quit()  # Exit the application

if __name__ == "__main__":
    unittest.main()
