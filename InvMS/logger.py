import os
from datetime import datetime


LOG_FOLDER = "logs"
LOG_FILE   = os.path.join(LOG_FOLDER, "activity.log")

# __ One-time initialisation flag ______________________________________________
# Previously initialize_logger() checked os.path.exists() on EVERY single call to log_action / read_logs / clear_logs.  We now do the check once at import time and cache the result, so disk I/O is minimal during normal operation.
# _____________________________________________________________________________

_logger_ready = False

def initialize_logger():
    # Ensure the logs folder and file exist.  Idempotent after first call.
    global _logger_ready

    if _logger_ready:
        return

    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("===== InvMS Activity Log =====\n\n")

    _logger_ready = True

# WRITE LOG
def log_action(action, details=""):
    initialize_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build the entry as a single string and write in one call
    # (fewer OS-level write() syscalls than multiple f.write() calls)

    lines = [f"[{timestamp}]\n", f"Action  : {action}\n"]

    if details:
        lines.append(f"Details : {details}\n")

    lines.append("-" * 60 + "\n")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("".join(lines))

# READ LOGS
def read_logs():
    initialize_logger()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()

# CLEAR LOGS
def clear_logs():
    initialize_logger()
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("===== InvMS Activity Log =====\n\n")
    return True

# GET LOG FILE PATH
def get_log_file():
    initialize_logger()
    return LOG_FILE

# TEST
if __name__ == "__main__":
    log_action("SYSTEM START", "Inventory Application Started")
    print(read_logs())