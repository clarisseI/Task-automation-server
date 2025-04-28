# 🚀 Automated Task Scheduler

A web-based automation server allowing users to schedule system tasks (lock screen, restart, clean cache, mute volume, etc.)  
Supports **one-time** and **recurring** executions for macOS, Linux, and Windows!

---

## 📋 Features

- ✅ Schedule tasks immediately or at a future time
- 🔁 Support for recurring tasks (daily, weekly, monthly)
- 📡 Live task status polling
- 🖥️ OS-specific system command execution
- 🔒 Safe and logged command execution
- 🌐 Web frontend built with vanilla HTML/CSS/JS
- 🛠️ Backend powered by Flask + SQLite + APScheduler

---

## 🛠️ Tech Stack

| Frontend | Backend | Scheduler | Database | OS Commands |
|:---|:---|:---|:---|:---|
| HTML/CSS/JS | Python (Flask) | APScheduler | SQLite3 | OS Shell |

---

## 🚀 Project Structure

```bash
task-automation-server/
├── app.py               # Main Flask application
├── scheduler.py         # Task scheduling logic
├── db.py                # Database operations (SQLite)
├── command.py           # Load and parse system tasks
├── task_executor.py     # Secure system command execution
├── static/              # Frontend static files (CSS, JS)
│   ├── style.css
│   └── script.js
├── templates/
│   └── index.html       # Main client page
├── tasks.json           # All available tasks by OS
├── Automatedtask.db     # SQLite database (auto-created)
└── requirements.txt     # Python dependencies
---

## 📦 How to Run Locally

```bash
# 1. Clone the project
git clone https://github.com/yourusername/task-automation-server.git
cd task-automation-server

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python app.py

# Server will run on http://localhost:5001
