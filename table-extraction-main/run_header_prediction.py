import sys
import json
import os
import pandas as pd
from header_prediction import predict_config
import tqdm

def run_batch(test_folder, save_results_to, run_max):
    samples = json.loads(open(os.path.join(test_folder, 'data.json')).read())
    images_folder = os.path.join(test_folder, 'images')

    results = []
    for s, sample in enumerate(tqdm.tqdm(samples)):
        if s > run_max:
            break
        image_path = os.path.join(images_folder, sample['image'])
        prediction = predict_config(image_path)
        if prediction is not None:
            results.append({
                'predicted_entity' : prediction['entity'],
                'predicted_statCategory' : prediction['statCategory'],
                'predicted_statistic' : prediction['statistic'],
                'predicted_statPeriod' : prediction['statPeriod'],
                'entity' : sample['entity'],
                'statCategory' : sample['statCategory'],
                'statPeriod' : sample['statPeriod'],
                'statistic': sample['statistic'],
                'image' : image_path,
            })

    df = pd.DataFrame(results)
    df.to_csv(save_results_to)

    return df

if __name__ == '__main__':
    test_folder = sys.argv[1]
    save_results_to = sys.argv[2]
    run_max = int(sys.argv[3])

    run_batch(test_folder, save_results_to, run_max)