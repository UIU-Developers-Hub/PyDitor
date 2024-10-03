#E:\UDH\Compiler\ui\documentation_sidebar.py

from PyQt6.QtWidgets import QDockWidget, QTextBrowser  # Import QDockWidget and QTextBrowser
from PyQt6.QtCore import Qt

class DocumentationSidebar(QDockWidget):
    def __init__(self):
        super().__init__("Documentation")
        self.text_browser = QTextBrowser()
        self.setWidget(self.text_browser)
        self.setFixedWidth(300)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.hide()  # Initially hide the sidebar

    def set_widget_content(self, content):
        """Set the content of the documentation sidebar."""
        if content:
            formatted_content = self.format_documentation(content)
            self.text_browser.setHtml(formatted_content)
        else:
            self.text_browser.setPlainText("No documentation available.")
            self.hide()  # Hide if there's no content

    def format_documentation(self, content):
        """Format the documentation content for better readability."""
        return f"<h2 style='color: #ffffff;'>Documentation</h2><p style='color: #ffffff;'>{content}</p>"
