import json
import threading
import os

PROGRESS_DIR = "/tmp1/progress"
PROGRESS_FILE = os.path.join(PROGRESS_DIR, "progress.json")

# Ensure the directory exists
os.makedirs(PROGRESS_DIR, exist_ok=True)

progress_lock = threading.Lock()

def update_progress(college_name, stage, images_done=None, total_images=None):
    progress_data = {
        "college_name": college_name,
        "stage": stage,
        "images_processed": f"{images_done}/{total_images}" if images_done and total_images else "N/A"
    }

    print(f"📝 DEBUG: Writing progress to {PROGRESS_FILE}")

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f, indent=4)
