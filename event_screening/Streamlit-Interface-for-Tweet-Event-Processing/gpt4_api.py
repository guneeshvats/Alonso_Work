import openai

API_KEY = "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"

client = openai.OpenAI(api_key=API_KEY)

def get_gpt4_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful SQL expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()