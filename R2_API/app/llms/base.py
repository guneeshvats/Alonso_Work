import abc
import os

class BaseLLMConnector(abc.ABC):
    """
    Abstract Base Class defining the interface for Language Learning Model (LLM) connectors.
    
    This class serves as a template for implementing connectors to various LLM services
    like OpenAI, Google Gemini, Groq etc. All LLM connector implementations must inherit
    from this base class and implement its abstract methods.

    Attributes:
        api_key (str): Authentication key for the LLM service provider's API
    """

    def __init__(self, api_key: str):
        """
        Initialize a new LLM connector instance.

        Args:
            api_key (str): The API key for authenticating with the LLM service.
                          This should be obtained from the service provider.

        Raises:
            ValueError: If the API key is not provided or invalid.
        """
        self.api_key = api_key
        self.validate_api_key()

    def validate_api_key(self):
        """
        Validates that an API key has been provided.

        This method performs basic validation to ensure an API key exists before
        attempting to connect to any LLM service.

        Raises:
            ValueError: If the API key is None, empty, or otherwise invalid.
        """
        if not self.api_key:
            raise ValueError("API key is required to initialize the LLM Connector.")

    @abc.abstractmethod
    def generate_response(self, prompt: str, **kwargs):
        """
        Generate a response from the LLM based on the provided prompt.

        This abstract method must be implemented by all concrete connector classes.
        The implementation should handle the specific API calls and response processing
        for the particular LLM service being used.

        Args:
            prompt (str): The input text prompt to send to the LLM
            **kwargs: Additional keyword arguments that may be required by specific
                     LLM implementations (e.g., temperature, max_tokens, etc.)

        Returns:
            The response from the LLM. The exact return type should be documented
            in the implementing class.

        Raises:
            NotImplementedError: If the implementing class does not override this method
        """
        pass