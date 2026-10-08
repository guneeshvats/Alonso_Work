import sys
import os
import json
import random
import shutil
import tqdm 

root_folder = "../Table Extraction/data"

images_folder = os.path.join(root_folder, "ImageFiles")
json_folder = os.path.join(root_folder, "JsonFiles")

target_json_folder = "datasets/pdf2text_v1/"
target_images_folder = "datasets/pdf2text_v1/images"
colleges = ['Arkansas', 'Maryland', 'Vanderbilt']

num_samples_from_each = 35

def run():
    num_images = 1
    final_json = []
    for college in colleges:
        college_image_folder = os.path.join(images_folder, college)
        college_json_data = open(os.path.join(json_folder, f"{college}_gold_dataset.jsonl")).readlines()
        #college_json = json.loads()

        print(college_image_folder, len(college_json_data))

        random_set = list(college_json_data)
        random.shuffle(random_set)

        random_set = [json.loads(x) for x in random_set[:num_samples_from_each]]

        for i in tqdm.tqdm(range(len(random_set))):

            image_file = random_set[i]["boundingBoxImage"]
            image_extension = image_file.split('.')[-1]
            image_path = os.path.join(college_image_folder, image_file)
            target_image_name = f"{num_images}.{image_extension}"
            target_image_path = os.path.join(target_images_folder, target_image_name )

            shutil.copyfile(image_path, target_image_path)
            dp = {}
            dp["image"] = target_image_name
            dp["entity"] = random_set[i]["entity"]
            dp["statCategory"] = random_set[i]["statCategory"]
            dp["statistic"] = random_set[i]["statistic"]
            dp["statPeriod"] = random_set[i]["statPeriod"]

            final_json.append(dp)


            num_images += 1

    with open(os.path.join(target_json_folder, "data.json"), "w") as w:
        w.write(json.dumps(final_json, indent=4))

    print("Done !")

if __name__ == "__main__":
    run()
        
    