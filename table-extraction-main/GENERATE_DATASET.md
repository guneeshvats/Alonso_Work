# README

## Dataset Creation Script for Sports Table Extraction

This script creates a dataset by randomly sampling a specified number of sports records from multiple JSON files, copying the corresponding image files, and saving both the image and record information into a new target directory. The dataset is created from the specified set of colleges, and the results are saved in a format suitable for further use in machine learning or data processing tasks.

### Features

- Randomly selects a specified number of records from multiple JSON files for each college.
- Copies the corresponding images to a target folder.
- Writes a new `data.json` file with relevant information for each sampled record (entity, stat category, statistic, stat period) and the corresponding image name.
- Organizes the output into a new dataset structure.

### Requirements

1. **Python 3.x**
2. **Required Libraries**:
   - `tqdm`
   - `os`
   - `json`
   - `random`
   - `shutil`

You can install the required dependencies by running:

```bash
pip install tqdm
```

### Input

1. **Source Directories**:
   - `ImageFiles`: This folder contains the images for different colleges.
   - `JsonFiles`: This folder contains JSONL files with sports records corresponding to the images.

2. **JSONL Files**: Each JSONL file contains multiple sports records in JSON format for a specific college. Each record includes:
   - `boundingBoxImage`: The image file name.
   - `entity`: The entity (e.g., Player or Team).
   - `statCategory`: The category of the statistic (e.g., Passing, Rushing).
   - `statistic`: The specific statistic (e.g., Yards, Touchdowns).
   - `statPeriod`: The period for the statistic (e.g., Game, Season, Career).

### Output

1. **Target Directory Structure**:
   - The images and corresponding records are saved in the target directory `datasets/pdf2text_v1/`.
   - Images are saved in `datasets/pdf2text_v1/images/`.
   - The final `data.json` file is saved in `datasets/pdf2text_v1/`.

2. **data.json**: A JSON file containing the sampled sports records. Each record has the following fields:
   - `image`: The image file name.
   - `entity`: The entity type.
   - `statCategory`: The sports category.
   - `statistic`: The specific statistic.
   - `statPeriod`: The period of the statistic.

### Configuration

The following parameters can be customized in the script:

- **root_folder**: The path to the source folder containing the `ImageFiles` and `JsonFiles` directories.
- **target_json_folder**: The path where the final JSON data will be saved.
- **target_images_folder**: The path where the images will be saved.
- **colleges**: A list of college names for which records will be sampled (e.g., `['Arkansas', 'Maryland', 'Vanderbilt']`).
- **num_samples_from_each**: The number of records to sample from each college's JSON file.

### How to Use

1. **Prepare Input Data**: Ensure that the following directory structure is in place:
   ```
   Table Extraction/
   ├── data/
       ├── ImageFiles/
       │   ├── Arkansas/
       │   ├── Maryland/
       │   └── Vanderbilt/
       └── JsonFiles/
           ├── Arkansas_gold_dataset.jsonl
           ├── Maryland_gold_dataset.jsonl
           └── Vanderbilt_gold_dataset.jsonl
   ```

2. **Run the Script**:

   To run the script, execute the following command in your terminal:

   ```bash
   python <script_name>.py
   ```

3. **Output**: The script will copy the images and generate the `data.json` file in the target directory `datasets/pdf2text_v1/`.

### Example Output

After running the script, the target folder will have the following structure:

```
datasets/
└── pdf2text_v1/
    ├── images/
    │   ├── 1.jpg
    │   ├── 2.jpg
    │   └── ...
    └── data.json
```

The `data.json` file will contain records similar to:

```json
[
    {
        "image": "1.jpg",
        "entity": "Player",
        "statCategory": "Passing",
        "statistic": "Yards",
        "statPeriod": "Game"
    },
    {
        "image": "2.jpg",
        "entity": "Team",
        "statCategory": "Rushing",
        "statistic": "Touchdowns",
        "statPeriod": "Season"
    },
    ...
]
```

### Notes

- Ensure that the paths in the script are correctly set to your local environment.
- The script will sample a specified number of records from each college's JSON file. You can modify the `num_samples_from_each` parameter to control how many samples are taken.
- The script uses `shutil.copyfile` to copy image files, so ensure you have sufficient disk space in the target folder.

### Error Handling

- The script will skip any records for which the corresponding image file is not found.
- Ensure that the JSONL files and images are correctly named and placed in the appropriate folders.G