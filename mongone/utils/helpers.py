import os
from rich.console import Console

console = Console()


def validate_file_exists(file_path):
    """Check if the specified file exists."""
    return os.path.exists(file_path)


def get_cutoff_date(days):
    """Calculate the cutoff date based on the provided number of days."""
    from datetime import datetime, timedelta

    return datetime.now().replace(tzinfo=None) - timedelta(days=days)


class Console:
    """Wrapper for rich Console to use throughout the application."""

    def __init__(self):
        self.console = console

    def print(self, message, style=None):
        """Print messages to the console."""
        if style:
            self.console.print(message, style=style)
        else:
            self.console.print(message)
