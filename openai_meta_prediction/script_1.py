import base64
import requests
import sys
import json

# OpenAI API Key
api_key = json.loads(open("header_prediction_config.json").read())["api_key"]

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def predict_config(image_path):
    # Getting the base64 string
    base64_image = encode_image(image_path)

    PROMPT = """
    Given the above image, your task is to predict the following information for the table marked in red border in the image. 

    Note that the image has information about sports records. It has a main header, followed by a series of subheaders. The image is also split into columns. So, please take that into consideration. Predict the following data accurately.

    Please give output in the following JSON format:

    {
         "entity" : "",
         "statCategory" : "",
         "statistic" : "",
         "statPeriod" : ""
    }

     Here are all the allowed values for entity field : Player, Team

     Here are all the allowed values for the statCategory field : Defense , Field Goals , Kickoff Returns , Offense , PATs , Passing , Punt Returns , Punt , Receiving , Rushing , Scoring , Special Teams

     Here are all the allowed values for the statistic field : Attempted , Attempts , Completed , First Downs , Fumble , Interceptions , Long , Made , Plays , Points , Receptions , Sacks(Total) , Tackles for Loss , Tackles(Total) , Touchdowns , Yards

     Here are all the allowed values for the statPeriod field: Game, Season, Career

     Only predict the information contained within the image. If you cannot detect any property, just fill it with null. Remember that you can fill in a field only with the list of values allowed for the field. Pay attention to the sequence in which the table occurs, as that determines information necessary for this task. 

     Important ! : For this purpose, only consider the headers which occur before the table and not after it.

     Generate only JSON. It should be parseable by a program later on. DO NOT format the JSON in any markdown.
     """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    try:
        message = response.json()
        message = message["choices"][0]["message"]["content"]

        try:
            json_message = json.loads(message)
        except Exception as e:
            if 'json' in message:
                message = message.replace('json', '').replace('`', '')
            return json.loads(message)


    except Exception as e:
        return None


if __name__ == "__main__":
    # Path to your image
    image_path = sys.argv[1]

    config = predict_config(image_path)
    print(config)