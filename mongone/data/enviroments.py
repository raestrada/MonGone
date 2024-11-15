import re
from rich.console import Console

console = Console()


def detect_environment(project_name, patterns):
    """Detect the environment of a given project based on its name."""
    for env, pattern in patterns.items():
        if re.search(pattern, project_name, re.IGNORECASE):
            return env
    return "unknown"
