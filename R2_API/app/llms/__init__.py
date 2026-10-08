from .base import BaseLLMConnector
from .gemini_connector import GeminiConnector
from .groq_connector import GroqConnector
from .openai_connector import OpenAIConnector
from enum import Enum  #StrEnum


class LLMConnectors(Enum):
    """
    Enumeration of supported Language Learning Model connectors.

    This enum defines the available LLM service providers that can be used
    to connect to various language models.

    Attributes:
        BASE: Base connector class (primarily for testing/development)
        OPENAI: OpenAI API connector
        GEMINI: Google's Gemini API connector  
        GROQ: Groq API connector
    """
    BASE = "base"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"


class LLMModels(Enum):
    """
    Enumeration of supported Language Learning Models across different providers.

    This enum defines the specific model versions available from each provider,
    allowing for precise model selection when making API calls.

    Attributes:
        BASE: Base model class (primarily for testing/development)
        GPT4: OpenAI's GPT-4 model
        GPT_MINI: Lightweight version of GPT-4
        GEMINI_FLASH: Google's Gemini 2.0 Flash model
        GEMINI_FLASH_LITE: Lightweight version of Gemini Flash
        LLAMA_1: Meta's Llama 3.2 1B preview model
        LLAMA_8: Meta's Llama3 8B model
        LLAMA_70: Meta's Llama 3.3 70B versatile model
        GEMMA: Google's Gemma 2 9B instruction-tuned model
    """
    BASE = "base"
    GPT4 = "gpt-4o"
    GPT_MINI = "gpt-4o-mini"
    GEMINI_FLASH = "gemini-2.0-flash"
    GEMINI_FLASH_LITE = "gemini-2.0-flash-lite"
    LLAMA_1 = "llama-3.2-1b-preview"
    LLAMA_8 = "llama3-8b-8192"
    LLAMA_70 = "llama-3.3-70b-versatile"
    GEMMA = "gemma2-9b-it"
    GPT4_1_NANO = "gpt-4.1-nano"
    GPT4_1_MINI = "gpt-4.1-mini"
    GPT4_1 = "gpt-4.1"
    GPT_O4_MINI = "o4-mini-2025-04-16"



def get_llm_connector(connector: LLMConnectors, model: LLMModels):
    """
    Factory function to instantiate the appropriate LLM connector based on provider and model.

    Args:
        connector (LLMConnectors): The LLM service provider to connect to
        model (LLMModels): The specific model version to use

    Returns:
        BaseLLMConnector: An instance of the appropriate connector class configured
                         for the specified model

    Raises:
        ValueError: If an unsupported connector type is specified
        
    Example:
        >>> connector = get_llm_connector(LLMConnectors.OPENAI, LLMModels.GPT4)
        >>> response = connector.generate_text("Hello, world!")
    """
    # Base connector currently disabled for production
    # if connector == LLMConnectors.BASE:
    #     return BaseLLMConnector()
    
    if connector == LLMConnectors.OPENAI:
        print(f"I am using OpenAI API with model = {model}")
        return OpenAIConnector(model.value)
    elif connector == LLMConnectors.GEMINI:
        return GeminiConnector(model.value)
    elif connector == LLMConnectors.GROQ:
        return GroqConnector(model.value)
    else:
        raise ValueError(f"Unsupported LLM connector: {connector}")
