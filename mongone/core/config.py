import os
import yaml

CONFIG_FILE = "mongone.yaml"


def load_config():
    """Load configuration from the config file."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(
            f"Configuration file '{CONFIG_FILE}' not found. Run 'mongone init' first."
        )
    with open(CONFIG_FILE, "r") as file:
        return yaml.safe_load(file)


def save_config(config):
    """Save configuration to the config file."""
    with open(CONFIG_FILE, "w") as file:
        yaml.dump(config, file)
