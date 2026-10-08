import google.generativeai as genai
import os
from dotenv import load_dotenv
from app.llms.base import BaseLLMConnector
from app.constants import LLMModels

# Load environment variables
# dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv()


class GeminiConnector(BaseLLMConnector):
    """
    OpenAI GPT-4o Connector, inheriting from BaseLLMConnector.
    """

    def __init__(self, model: str | None = LLMModels.GEMINI_FLASH.value):
        """
        Initializes the OpenAI GPT-4o connector.
        """
        self.model = model
        self.api_key = os.getenv(LLMModels.GEMINI_API_KEY.value)
        if not self.api_key:
            raise ValueError("API key is missing. Make sure it's set in the .env file or environment variables.")

        super().__init__(self.api_key)
        self.client = genai.Client(api_key=self.api_key)  # New API Client

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
            response = self.client.models.generate_content(
                model = self.model,
                contents = user_prompt
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")


# === Test the OpenAIConnector when running this script directly ===
if __name__ == "__main__":
    gemini_llm = GeminiConnector()

    user_prompt = "Give me a nice romantic poem."

    # Test with custom system prompt
    response_custom = gemini_llm.generate_response(user_prompt, system_prompt="Explain concepts in simple terms.")

    # Test with default system prompt
    response_default = gemini_llm.generate_response(user_prompt)

    print("\n=== Gemini GPT-4o Response (Custom System Prompt) ===")
    print(response_custom)

    print("\n=== Gemini GPT-4o Response (Default System Prompt) ===")
    print(response_default)
