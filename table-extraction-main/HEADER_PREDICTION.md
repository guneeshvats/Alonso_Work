# README

## Table Prediction and Batch Processing Script

This repository provides a solution to predict sports-related table data from images and process these images in batch mode. The predictions are made using the OpenAI API, and the results are compared against ground truth data. The results are saved in a CSV format, which can be used for further analysis.

### Features

- Predicts table data such as entity type, stat category, statistics, and stat period from an image.
- Batch processes multiple images and saves the prediction results to a CSV file.
- Uses the GPT-4 API from OpenAI to make predictions based on the visual input (image).
- Compares predictions with ground truth data for evaluation.
- Generates a CSV file containing both predictions and actual values for further analysis.

### Requirements

1. **Python 3.x**
2. **OpenAI API Key**: A valid API key for accessing OpenAI models is required.
3. **Required Libraries**:
   - `requests`
   - `json`
   - `base64`
   - `pandas`
   - `tqdm`

You can install the required dependencies by running:

```bash
pip install requests pandas tqdm
```

4. **header_prediction.py**: Ensure that the `header_prediction.py` script is available in the same directory or installed as a module. This script contains the `predict_config(image_path)` function that makes predictions based on image input using the OpenAI API.

### Input Files

1. **data.json**: A JSON file containing ground truth data and corresponding image names. This file should be located in the `test_folder` directory. The structure of the JSON file is as follows:

    ```json
    [
      {
        "image": "image_001.jpg",
        "entity": "Player",
        "statCategory": "Passing",
        "statistic": "Yards",
        "statPeriod": "Game"
      },
      ...
    ]
    ```

2. **Images Folder**: A folder named `images` within the `test_folder` directory that contains the images referenced in the `data.json` file. Each image should follow the naming convention provided in `data.json` (e.g., `image_001.jpg`).

3. **header_prediction_config.json**: A configuration file containing your OpenAI API key. Example structure:

   ```json
   {
     "api_key": "your_openai_api_key"
   }
   ```

### Workflow

1. **Image Encoding**: The `encode_image` function converts the image into a base64 string, which is then passed to the OpenAI API for prediction.

2. **Prediction**: The `predict_config` function sends the base64-encoded image to the OpenAI API along with a custom prompt, and returns the predicted sports-related data in JSON format. The prediction includes:
   - `entity`: The predicted entity (Player or Team).
   - `statCategory`: The predicted stat category (e.g., Passing, Rushing).
   - `statistic`: The predicted statistic (e.g., Yards, Touchdowns).
   - `statPeriod`: The predicted stat period (e.g., Game, Season, Career).

3. **Batch Processing**: The `run_batch` function processes multiple images in batch mode. It reads the ground truth data from `data.json`, makes predictions for each image, and saves the results to a CSV file.

4. **Output**: The results from batch processing are saved in a CSV file that includes both the predictions and actual values for comparison.

### Output

- The CSV file generated will have the following columns:
  - `predicted_entity`: The predicted entity type (e.g., Player, Team).
  - `predicted_statCategory`: The predicted stat category (e.g., Passing, Rushing).
  - `predicted_statistic`: The predicted statistic (e.g., Yards, Touchdowns).
  - `predicted_statPeriod`: The predicted stat period (e.g., Game, Season).
  - `entity`: The actual entity from `data.json`.
  - `statCategory`: The actual stat category from `data.json`.
  - `statistic`: The actual statistic from `data.json`.
  - `statPeriod`: The actual stat period from `data.json`.
  - `image`: The image file path.

### How to Use

1. **Prepare Input Data**:
   - Ensure you have a folder structure as follows:
     ```
     test_folder/
       ├── data.json
       └── images/
           ├── image_001.jpg
           ├── image_002.jpg
           └── ...
     ```

2. **Create a Configuration File**: You need a `header_prediction_config.json` file containing your OpenAI API key:

   ```json
   {
     "api_key": "sk-YOUR_OPENAI_API_KEY"
   }
   ```

3. **Run Batch Processing**:

   To run batch prediction, use the following command:

   ```bash
   python run_batch.py <test_folder> <save_results_to> <run_max>
   ```

   Example:

   ```bash
   python run_batch.py ./test_data ./results/predictions.csv 100
   ```

   - `test_folder`: Path to the folder containing `data.json` and the `images` folder.
   - `save_results_to`: Path to the CSV file where results will be saved.
   - `run_max`: Maximum number of samples to process from the dataset.

4. **Single Image Prediction**:
   
   For a single image, use the `predict_config` function directly from `header_prediction.py`:

   ```python
   from header_prediction import predict_config
   image_path = './images/image_001.jpg'
   prediction = predict_config(image_path)
   print(prediction)
   ```

### Example Input and Output

Given a folder structure like this:

```
test_data/
  ├── data.json
  └── images/
      ├── image_001.jpg
      └── image_002.jpg
```

And `data.json` containing:

```json
[
  {
    "image": "image_001.jpg",
    "entity": "Player",
    "statCategory": "Passing",
    "statistic": "Yards",
    "statPeriod": "Game"
  },
  {
    "image": "image_002.jpg",
    "entity": "Team",
    "statCategory": "Rushing",
    "statistic": "Touchdowns",
    "statPeriod": "Season"
  }
]
```

Running the command:

```bash
python run_batch.py ./test_data ./results/predictions.csv 100
```

Will generate a CSV file at `./results/predictions.csv` with columns for both the predicted and actual values.

### Notes

- Ensure the image files exist and match the names in `data.json`.
- If `predict_config` fails for any reason (e.g., OpenAI API issues, file path issues), the corresponding sample will be skipped.
- The `run_max` parameter allows you to limit the number of samples processed. If `run_max` is smaller than the number of samples in `data.json`, only that many samples will be processed.

### Error Handling

- If the API key is missing or invalid, the script will not be able to connect to the OpenAI API.
- If the image path is invalid or an image is missing, the script will skip that sample and continue processing the remaining images.
