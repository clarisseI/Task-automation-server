"""
command.py
-----------

Handles loading and parsing of available system tasks from a JSON configuration file.

Provides:
- load_tasks(): Load all tasks from tasks.json
- get_os_command(): Retrieve the command string for a given task and OS
- get_all_command_names(): List all available task names for a specific OS
"""

import json
import os

# Dynamically find tasks.json location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMAND_FILE = os.path.join(BASE_DIR, "tasks.json")


def load_tasks():
    """
    Load the tasks from the JSON configuration file.

    Returns:
        dict: Parsed dictionary of available tasks organized by category and OS.

    Raises:
        FileNotFoundError: If tasks.json does not exist.
        ValueError: If the JSON file is malformed.
    """
    if not os.path.exists(COMMAND_FILE):
        raise FileNotFoundError("tasks.json not found.")

    with open(COMMAND_FILE, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError("tasks.json contains invalid JSON.") from e
    return data

def get_os_command(os_type, task_name):
    """
    Retrieve the OS-specific shell command for a given task.

    Args:
        os_type (str): One of 'mac', 'linux', 'windows'.
        task_name (str): Name of the task.

    Returns:
        str or None: The shell command to execute, or None if not found.
    """
    tasks = load_tasks()
    for category, os_map in tasks.items():
        if os_type in os_map and task_name in os_map[os_type]:
            return os_map[os_type][task_name]
    return None

def get_all_command_names(os_type):
    """
    Retrieve all available task names for a specific OS.

    Args:
        os_type (str): One of 'mac', 'linux', 'windows'.

    Returns:
        list: List of task names supported for the OS.
    """
    tasks = load_tasks()
    available = []
    for category, os_map in tasks.items():
        if os_type in os_map:
            available.extend(os_map[os_type].keys())
    return available
