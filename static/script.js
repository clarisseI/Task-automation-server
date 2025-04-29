document.addEventListener("DOMContentLoaded", () => {

  const BASE_URL =  'http://10.55.60.39:5001'


    const categorySelect = document.getElementById("category");
    const taskSelect = document.getElementById("task");
    const statusText = document.getElementById("status");
    const scheduledTimeInput = document.getElementById("scheduled_time");
    const recurrenceSelect = document.getElementById("recurrence");
    const taskForm = document.getElementById("taskForm");

    // Set minimum datetime to now
    function getLocalISOTime() {
      const now = new Date();
      const tzoffset = now.getTimezoneOffset() * 60000;
      const localISOTime = new Date(now - tzoffset).toISOString().slice(0, 16);
      return localISOTime;
  }

  function setMinDateTime() {
      scheduledTimeInput.min = getLocalISOTime();
  }
  // Set minimum datetime to now
  function parseLocalDateTime(input) {
    const [datePart, timePart] = input.split('T');
    const [year, month, day] = datePart.split('-').map(Number);
    const [hour, minute] = timePart.split(':').map(Number);
    return new Date(year, month - 1, day, hour, minute);
}
    // Show toast notifications
    function showToast(message, duration = 2000) {
      const toast = document.getElementById('toast');
      const timeNow = new Date().toLocaleTimeString();
  

      console.groupCollapsed(`[${timeNow}] ${message}`);
      console.log(`Message: ${message}`);
      console.log(`Timestamp: ${timeNow}`);
      console.groupEnd();
  
  
      toast.textContent = message;
      toast.style.display = 'block';
      toast.style.opacity = '1';
  
      setTimeout(() => {toast.style.opacity = '0';}, duration - 500);
      setTimeout(() => {toast.style.display = 'none';}, duration);
  }
  
    // Poll task status
    function pollTaskStatus(jobId, maxDuration = 300000, delay = 1000) {
      const maxAttempts = Math.floor(maxDuration / delay);
      let attempts = 0;
      let lastStatus = null;  
    
      const poll = () => {
        fetch(`${BASE_URL}/task_status/${jobId}`)
          .then(res => res.json())
          .then(data => {
            const currentStatus = data.status;

                if (currentStatus !== lastStatus) {
                    const timeNow = new Date().toLocaleTimeString();
                    console.groupCollapsed(`[${timeNow}] 📡 Polling update`);
                    console.log(`Status changed: ${lastStatus} ➔ ${currentStatus}`);
                    console.log(data);
                    console.groupEnd();

                    lastStatus = currentStatus;  // Update last status
                }
    
            if (currentStatus === 'completed' || currentStatus === 'recurring') {
              if (data.next_time) {
                const prettyNextRun = new Date(data.next_time).toLocaleString('en-US', {
                  weekday: 'long', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true
              });
                showToast(`✅ Task completed. Next run scheduled at ${prettyNextRun}`);
              } else {
                showToast("✅ Task completed.");
                      }
                    
              return;
            }
    
            if (data.status === 'failed') {
              showToast("❌ Task failed.");
              return;
            }
    
            attempts++;
            if (attempts < maxAttempts) {
              setTimeout(poll, delay);
            } else {
              showToast("⚠️ Task status timeout. It may have finished shortly after.");
            }
          })
          .catch(err => {
            console.error("Status check error:", err);
            showToast("⚠️ Could not check task status.");
          });
      };
    
      setTimeout(poll, delay * 1.5);
    }
  // Initialize min datetime
    setMinDateTime();
    setInterval(setMinDateTime, 60000); // Update every minute

   // Live-clear errors
categorySelect.addEventListener('change', () => {
  document.getElementById('category-error').textContent = '';
});

taskSelect.addEventListener('change', () => {
  document.getElementById('task-error').textContent = '';
});


scheduledTimeInput.addEventListener('input', () => {
  document.getElementById('time-error').textContent = '';
});

// Fetch available tasks and setup category/task select
  fetch(`http://10.55.60.39:5001/list_tasks`)
  .then((res) => res.json())
  .then((data) => {
    const availableTasks = data.available_tasks;

    Object.keys(availableTasks).forEach((category) => {
      const opt = document.createElement("option");
      opt.value = category;
      opt.textContent = category;
      categorySelect.appendChild(opt);
    });

    categorySelect.addEventListener("change", () => {
      const selectedCategory = categorySelect.value;
      const tasks = availableTasks[selectedCategory];

      taskSelect.innerHTML = "<option value=''>Select a task</option>";
      taskSelect.disabled = true;

      if (tasks && tasks.length > 0) {
        tasks.forEach((cmd) => {
          const cmdOpt = document.createElement("option");
          cmdOpt.value = cmd;
          cmdOpt.textContent = cmd;
          taskSelect.appendChild(cmdOpt);
        });

        taskSelect.disabled = false;
      } else {
        taskSelect.disabled = true;
      }
    });
  })
  .catch((err) => {
    console.error("Failed to fetch task:", err);
    statusText.textContent = "Error loading tasks.";
  });

  // Handle task form submission
     taskForm.addEventListener('submit',(e)=>{
      e.preventDefault();

       // Clear old error messages
      document.getElementById('category-error').textContent = '';
      document.getElementById('task-error').textContent = '';
      document.getElementById('time-error').textContent = '';

      const category = categorySelect.value;
      const task = taskSelect.value;
      const scheduled_time = scheduledTimeInput.value;
      const recurrence = recurrenceSelect.value;
      let hasError = false;

      console.log('Submitting task:', { category, task, scheduled_time, recurrence });

      if (!category) {
        document.getElementById('category-error').textContent = "Please select a category.";
        etTimeout(() => errorEl.textContent = '', 1000);
        hasError = true;
     }
      if (!task) {
          document.getElementById('task-error').textContent = "Please select a task.";
          hasError = true;
      }
        
       // Validate scheduled time
       if (scheduled_time) {
        const selectedTime = parseLocalDateTime(scheduled_time);
        const now = new Date();

        if (selectedTime < now) {
          document.getElementById('time-error').textContent = "Scheduled time must be in the future.";
          hasError = true;
        }
    }
    if (hasError) {
      return; // 🚫 Don't submit if any error
  }
    
  if (!scheduled_time) {
    const timeError = document.getElementById('time-error');
    timeError.textContent = "⚡ No time selected. Task will execute immediately.";
    setTimeout(() => {
      timeError.textContent = ''; 
        submitNow(); // Submit after short delay
    }, 2000);

    return; 
}
     
     submitNow(); // Submit directly if time selected

     // --- Local function to actually submit the task ---
     function submitNow() {
        fetch(`${BASE_URL}/run_task`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task: task, 
            scheduled_time: scheduled_time || undefined, // only include if scheduled_time exists
            recurrence: recurrence,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.error) {
              showToast("❌ Error: " + data.error);
            } else {
              showToast("✅ " + data.message);
              pollTaskStatus(data.job_id);
              taskForm.reset();
                  setMinDateTime(); // Reset min datetime after form clears
                  document.getElementById('time-error').textContent = '';
                  document.getElementById('category-error').textContent = '';
                  document.getElementById('task-error').textContent = '';
            }
          })
          .catch((err) => {
            showToast("⚠️ Failed: " + err.message)
          });
        }
      });

    })
  
      
  