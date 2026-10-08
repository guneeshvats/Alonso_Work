#############################################################################################################################  
#                                    PROGRESS TRACKER FOR COLLEGE RECORD PROCESSING                                                  
#############################################################################################################################

'''
Purpose:
    - Tracks the progress of college record processing.
    - Stores progress updates in a JSON file.
    - Uses threading lock to prevent simultaneous write conflicts.

Key Features:
    - Creates a progress directory if it doesn't exist.
    - Logs the current stage of processing for a given college.
    - Tracks image processing progress when applicable.

Created by:
    Guneesh Vats
    ML Engineer, Alonzo

Dated:
    23rd Jan, 2024
    Thursday
'''

#############################################################################################################################
#                                                          IMPORTS                                                           
#############################################################################################################################
import json
import threading
import os


#############################################################################################################################
''' 
Initialize Progress Tracking:
    - Defines a directory and file path to store progress.
    - Ensures the directory exists before storing updates.
    - Uses a lock to avoid race conditions in concurrent processing.
'''
#############################################################################################################################
PROGRESS_DIR = "/tmp1/progress"
PROGRESS_FILE = os.path.join(PROGRESS_DIR, "progress.json")

# Ensure the directory exists
os.makedirs(PROGRESS_DIR, exist_ok=True)

progress_lock = threading.Lock()



#############################################################################################################################
''' 
Update Progress:
    - Updates the progress of a college's processing stage.
    - Saves progress in a JSON file for tracking.
    - Supports optional image processing tracking.
    
    Args:
        college_name (str): The name of the college being processed.
        stage (str): The current processing stage.
        images_done (int, optional): Number of images processed.
        total_images (int, optional): Total number of images.
    
    Example Progress Data:
    {
        "college_name": "Florida",
        "stage": "Processing Images",
        "images_processed": "5/20"
    }
'''
#############################################################################################################################
def update_progress(college_name, stage, images_done=None, total_images=None):
    progress_data = {
        "college_name": college_name,
        "stage": stage,
        "images_processed": f"{images_done}/{total_images}" if images_done and total_images else "N/A"
    }

    print(f" DEBUG: Writing progress to {PROGRESS_FILE}")

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f, indent=4)
