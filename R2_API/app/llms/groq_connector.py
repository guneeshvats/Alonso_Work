from groq import Groq
import os
from dotenv import load_dotenv
from app.llms.base import BaseLLMConnector
from app.constants import LLMModels

# Load environment variables
# dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv()


class GroqConnector(BaseLLMConnector):
    """
    OpenAI GPT-4o Connector, inheriting from BaseLLMConnector.
    """

    def __init__(self, model: str | None = LLMModels.LLAMA_8.value):
        """
        Initializes the OpenAI GPT-4o connector.
        """
        self.model = model
        self.api_key = os.getenv(LLMModels.GROQ_API_KEY.value)
        if not self.api_key:
            raise ValueError("API key is missing. Make sure it's set in the .env file or environment variables.")

        super().__init__(self.api_key)
        self.client = Groq(api_key=self.api_key)  # New API Client

    def generate_response(self, user_prompt: str, system_prompt: str = "You are an AI assistant",
                          temperature: float = 0.7):
        """
        Generates a response using OpenAI's GPT-4o.

        Args:
            system_prompt (str): Instructions to guide the assistant's behavior.
            user_prompt (str): The actual input query from the user.
            model (str): OpenAI model name (default: gpt-4o).
            temperature (float): Controls randomness (default: 0.7).

        Returns:
            str: The generated response from GPT-4o.
        """
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Groq API Error: {str(e)}")


# === Test the OpenAIConnector when running this script directly ===
if __name__ == "__main__":
    llm = GroqConnector()

    user_prompt = "Give me a nice romantic poem."

    # Test with custom system prompt
    response_custom = llm.generate_response(user_prompt, system_prompt="Explain concepts in simple terms.")

    # Test with default system prompt
    response_default = llm.generate_response(user_prompt)

    print("\n=== Gemini GPT-4o Response (Custom System Prompt) ===")
    print(response_custom)

    print("\n=== Gemini GPT-4o Response (Default System Prompt) ===")
    print(response_default)
