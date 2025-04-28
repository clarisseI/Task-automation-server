"""
scheduler.py
-------------

Handles background scheduling of system tasks using APScheduler.
Supports both one-time and recurring tasks with status tracking in memory and database.

Provides:
- start_scheduler(): Start the background APScheduler instance
- schedule_task(): Schedule a new task
- polling_scheduler(): Continuously update statuses of scheduled jobs

"""
import time
import threading
from datetime import datetime, timedelta
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError

from app.task_executor import execute_command
from app.db import update_task_status, get_all_tasks


task_status_cache = {}

# Set timezone to UTC
timezone = pytz.UTC

# Recurrence mapping for APScheduler
RECURRENCE_MAP = {
    "daily": {"days": 1},
    "weekly": {"weeks": 1},
    "hourly": {"hours": 1}
}

def start_scheduler():
    """
    Start and return a background scheduler instance.

    Returns:
        BackgroundScheduler: an active APScheduler instance
    """
    scheduler = BackgroundScheduler()
    scheduler.start()
    return scheduler

def schedule_task(scheduler, task, os_command, start_time, recurrence="none"):
    """
    Schedule a new task with APScheduler.

    Args:
        scheduler (BackgroundScheduler): The running scheduler instance
        task (str): The task name
        os_command (str): The system command to execute
        start_time (datetime): The scheduled start datetime
        recurrence (str): Recurrence type ('none', 'daily', 'weekly', 'hourly')

    Returns:
        str: The scheduled job_id
    """
    job_id = f"{task}_{int(start_time.timestamp())}"

    def task_wrapper():
        """
        Task execution wrapper that updates database and cache status.
        """
        now = datetime.now(timezone)
        update_task_status(job_id, "running", last_run=now)
        task_status_cache[job_id] = {"status": "running", "next_time": None}

        result = execute_command(task, os_command)

        job = scheduler.get_job(job_id)
        next_run = job.next_run_time.astimezone(timezone) if job and job.next_run_time else None

        if result["status"] == "success":
            if job and job.trigger.__class__.__name__ == "IntervalTrigger":
                new_status = "recurring"
            else:
                new_status = "completed"
            update_task_status(job_id, new_status, last_run=now, next_time=next_run)
            task_status_cache[job_id] = {"status": new_status, "next_time": next_run}
        else:
            update_task_status(job_id, "failed", last_run=now)
            task_status_cache[job_id] = {"status": "failed", "next_time": None}

    if recurrence == "none":
        scheduler.add_job(
            task_wrapper,
            trigger=DateTrigger(run_date=start_time),
            id=job_id,
            replace_existing=True
        )
    else:
        interval = RECURRENCE_MAP.get(recurrence.lower())
        scheduler.add_job(
            task_wrapper,
            trigger=IntervalTrigger(**interval, start_date=start_time),
            id=job_id,
            replace_existing=True
        )

    task_status_cache[job_id] = {"status": "pending", "next_time": start_time}
    update_task_status(job_id, "pending", next_time=start_time)
    return job_id

def polling_scheduler(scheduler, interval=5):
    """
    Background polling thread to monitor and sync job statuses.

    Args:
        scheduler (BackgroundScheduler): The running scheduler instance
        interval (int): How often to poll in seconds
    """

    def poll():
        while True:
            now = datetime.now(timezone)
            db_tasks = {t["job_id"] for t in get_all_tasks()}

            for job in scheduler.get_jobs():
                job_id = job.id
                next_run = job.next_run_time.astimezone(timezone) if job.next_run_time else None

                if job_id not in db_tasks:
                    continue  # Skip unknown tasks

                # Check if the job is recurring
                is_recurring = isinstance(job.trigger, IntervalTrigger)

                current_status = task_status_cache.get(job_id, {}).get("status")

                if not next_run:
                    if not is_recurring:
                        # Only mark one-time tasks completed if no next_run
                        update_task_status(job_id, "completed", last_run=now)
                        task_status_cache[job_id] = {"status": "completed", "next_time": None}
                else:
                    if current_status == "running":
                        # Only after it has run at least once, update to next status
                        new_status = "recurring" if is_recurring else "pending"
                        update_task_status(job_id, new_status, next_time=next_run)
                        task_status_cache[job_id] = {"status": new_status, "next_time": next_run}

            time.sleep(interval)

    thread = threading.Thread(target=poll, daemon=True)
    thread.start()

