"""
db.py
-----

Handles all database operations for the Automated Task Scheduler.
Uses SQLite to persist task metadata such as status, scheduled time, and recurrence information.

Provides:
- init_db(): Initialize the database and create tables
- insert_task(): Insert a new task record
- update_task_status(): Update the status of an existing task
- get_all_tasks(): Retrieve all tasks from the database

"""
import sqlite3
DB_NAME = "Automatedtask.db"

def init_db():
    """
    Initialize the database and create the 'tasks' table if it does not exist.
    """
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                job_id TEXT NOT NULL UNIQUE,
                is_recurring BOOLEAN,
                last_run TEXT,
                next_time TEXT
            )
        ''')
    conn.commit()
    
    conn.close()

def insert_task(task, status, scheduled_time, job_id, is_recurring, last_run, next_time):
    
    """
    Insert a new task into the database.

    Args:
        task (str): Task name
        status (str): Task status ('pending', 'running', 'completed', etc.)
        scheduled_time (datetime): Scheduled start time
        job_id (str): Unique job identifier
        is_recurring (bool): Whether the task is recurring
        last_run (datetime or None): Last execution time
        next_time (datetime or None): Next scheduled run time
    """
    if not is_recurring and last_run is None:
        last_run = scheduled_time  # First non-recurring task run = scheduled_time

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (task, status, scheduled_time, job_id, is_recurring, last_run, next_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        task,
        status,
        scheduled_time.isoformat(),
        job_id,
        is_recurring,
        last_run.isoformat() if last_run else None,
        next_time.isoformat() if next_time else None
    ))
    conn.commit()
    conn.close()

def update_task_status(job_id, status, last_run=None, next_time=None):
    """
    Update the status (and optionally last_run and next_time) of a task.

    Args:
        job_id (str): Unique job identifier
        status (str): New status ('pending', 'running', 'completed', 'failed', etc.)
        last_run (datetime or None): Time the task was last run
        next_time (datetime or None): Time of next scheduled run
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if last_run and next_time:
        c.execute('''
            UPDATE tasks
            SET status = ?, last_run = ?, next_time = ?
            WHERE job_id = ?
        ''', (status, last_run.isoformat(), next_time.isoformat(), job_id))
    else:
        c.execute('''
            UPDATE tasks
            SET status = ?
            WHERE job_id = ?
        ''', (status, job_id))
    conn.commit()
    conn.close()

def get_all_tasks():
    """
    Retrieve all tasks from the database.

    Returns:
        list: A list of dictionaries, each representing a task
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    rows = c.fetchall()
    conn.close()
    keys = ["id", "task", "status", "scheduled_time", "job_id", "is_recurring", "last_run", "next_time"]
    return [dict(zip(keys, row)) for row in rows]
