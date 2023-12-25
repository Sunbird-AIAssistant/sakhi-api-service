import os
from configparser import ConfigParser


def get_config_value(section, key, default=None):
    # Check if the key exists in the environment variables
    value = os.getenv(key, default)

    # If the key is not in the environment variables, try reading from a config file
    if value is None:
        config_file_path = 'config.ini'  # Update with your config file path
        config = ConfigParser()

        # Attempt to read the config file
        try:
            config.read(config_file_path)
            value = config.get(section, key, fallback=default)
        except Exception as e:
            print(f"Error reading config file: {e}")

    return value