"""
task_executor.py
-----------------

Handles executing system-level commands on the host machine.
Detects operating system and runs the appropriate shell commands securely.

Provides:
- get_os_type(): Detect current operating system
- execute_command(): Execute a system command with error handling and logging
"""
import subprocess
import platform
import logging
import platform


# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_os_type():
    """
    Detect the operating system the script is running on.

    Returns:
        str: One of 'mac', 'linux', 'windows', or 'unknown'
    """
    return {
        "darwin": "mac",
        "linux": "linux",
        "windows": "windows"
    }.get(platform.system().lower(), "unknown")

def validate_command(cmd):
    """
    Basic command validation for safety.
    Later: extend with real whitelisting if needed.
    """
    if not cmd or not isinstance(cmd, str):
        raise ValueError("Invalid command: must be a non-empty string.")
    return cmd

def execute_command(task_name, os_command):
    """
    Execute a shell command appropriate to the OS and capture the output.

    Args:
        task_name (str): A name used for logging (e.g., "restart computer")
        os_command (str): The command to execute as a string

    Returns:
        dict: Result object containing:
              - status: "success" or "error"
              - output: Command stdout if successful
              - error: Error message if failed
    """
    try:
        logging.info(f"Executing task: {task_name} | Command: {os_command}")
        result = subprocess.run(
            os_command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )

        logging.info(f"Task '{task_name}' executed successfully.")
        return {
            "status": "success",
            "output": result.stdout.strip(),
            "error": ""
        }

    except subprocess.CalledProcessError as e:
        logging.error(f"Task '{task_name}' failed: {e.stderr}")
        return {
            "status": "error",
            "output": "",
            "error": e.stderr.strip() if e.stderr else str(e)
        }

    except Exception as e:
        logging.exception("Unexpected error occurred while executing the task.")
        return {
            "status": "error",
            "output": "",
            "error": str(e)
        }
