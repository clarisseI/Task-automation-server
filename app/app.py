"""
app.py
-------

Main Flask application server for the Automated Task Scheduler project.

Provides APIs to:
- List available tasks
- Schedule one-time or recurring tasks
- Track execution status of scheduled tasks
"""

from flask import Flask, request, jsonify, render_template
from datetime import datetime
from app.scheduler import start_scheduler, schedule_task, polling_scheduler, task_status_cache
from app.db import init_db, insert_task, get_all_tasks
from app.command import load_tasks, get_os_command
from app.task_executor import get_os_type
import logging


log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


app = Flask(__name__)


# Initialize the database (creates tables if not present)
init_db()

# Start the background scheduler (for APScheduler-based recurring tasks)
scheduler = start_scheduler()

# Launch the polling thread to update job statuses
polling_scheduler(scheduler)

@app.route('/')
def home():
    """
    Render the home page for the frontend client.
    
    Returns:
        HTML page
    """
    return render_template('index.html')


@app.route('/list_tasks', methods=['GET'])
def list_tasks():
    
    """
    List all available system tasks that can be performed, filtered by OS.

    Returns:
        JSON object of available tasks
    """
    os_type = get_os_type()
    tasks = load_tasks()
    
    filtered = {
        category: list(os_map[os_type].keys())
        for category, os_map in tasks.items() if os_type in os_map
    }
    return jsonify({"available_tasks": filtered})


@app.route('/tasks', methods=['GET'])
def tasks():
    """
    Return all scheduled tasks from the database.

    Returns:
        JSON object containing task entries
    """
    return jsonify({"tasks": get_all_tasks()})

@app.route('/task_status/<job_id>', methods=['GET'])
def get_task_status(job_id):
    """
    Check the status and next run time of a specific scheduled task.

    Args:
        job_id (str): The ID of the scheduled task.

    Returns:
        JSON object with status and next run time
    """

    cache = task_status_cache.get(job_id)

    if cache:
        status = cache.get("status", "unknown")
        next_time = cache.get("next_time")
    else:
        status = "unknown"
        next_time = None

    tasks = get_all_tasks()
    task_detail = next((t for t in tasks if t["job_id"] == job_id), None)

    if task_detail:
        if not next_time:
            next_time = task_detail.get("next_time")
        if status == "unknown":
            status = task_detail.get("status", "unknown")

    return jsonify({
        "job_id": job_id,
        "status": status,
        "next_time": next_time
    })





@app.route('/run_task', methods=['POST'])
def run_task():
    """
    Schedule and execute a new system task immediately or in the future.

    Request body:
        task (str): Name of the task
        scheduled_time (str): ISO format datetime string (optional)
        recurrence (str): Recurrence type (none, daily, weekly, monthly)

    Returns:
        JSON object with task scheduling information
    """
    data = request.json
    task = data.get('task')
    raw_time = data.get('scheduled_time')
    recurrence = data.get('recurrence', 'none')

    if not task:
        return jsonify({'error': 'No task provided'}), 400

    # Get the current OS and command for that task
    os_type = get_os_type()
    os_command = get_os_command(os_type, task)

    if not os_command:
        return jsonify({'error': 'Invalid or unsupported command for this OS'}), 400

    # Convert time string to datetime object
    try:
        scheduled_dt = datetime.fromisoformat(raw_time) if raw_time else datetime.now()
    except ValueError:
        return jsonify({'error': 'Invalid datetime format'}), 400

    # Schedule the task using APScheduler
    job_id = schedule_task(
        scheduler=scheduler,
        task=task,
        os_command=os_command,
        start_time=scheduled_dt,
        recurrence=recurrence
    )

    # Store in SQLite DB
    status = 'scheduled' if recurrence == 'none' else 'recurring'
    is_recurring = recurrence != 'none'

    insert_task(
        task=task, 
        status=status, 
        scheduled_time=scheduled_dt,
        job_id=job_id,
        is_recurring=is_recurring, 
        last_run=None,
        next_time=scheduled_dt if is_recurring else None
        )
    message = "Task scheduled successfully."

    return jsonify({
        "message": message,
        "job_id": job_id,
        "recurrence": recurrence
        
    })
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"}), 200


# ------------------------------------
# RUN SERVER
# ------------------------------------

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
