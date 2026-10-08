# Documentation for `openai_connector.py`

# Technical Documentation for OpenAIConnector Script

## Overview

This Python script provides a connector to OpenAI's GPT-4o model, enabling users to generate text responses based on input prompts. It is designed to facilitate interaction with OpenAI's language model through a simple interface, allowing for customization of the model's behavior via system prompts and temperature settings.

## Dependencies

- **openai**: The script relies on the OpenAI Python client library to interact with OpenAI's API.
- **os**: Used to handle environment variables and file paths.
- **dotenv**: Utilized for loading environment variables from a `.env` file.
- **BaseLLMConnector**: A base class imported from `app.llms.base`, which the `OpenAIConnector` class extends.
- **LLMModels**: Imported from `app.constants`, likely containing model names and API keys as constants.

## Environment Setup

The script expects an API key for OpenAI to be set as an environment variable, which can be loaded from a `.env` file using `dotenv`. This key must be stored under a constant defined in `LLMModels`.

## Class: OpenAIConnector

### Description

`OpenAIConnector` is a class that extends `BaseLLMConnector` and is responsible for interfacing with the OpenAI GPT-4o model. It manages the initialization of the API connection and provides a method to generate responses from the language model.

### Constructor: `__init__(self, model: str | None = LLMModels.GPT4.value)`

- **Purpose**: Initializes the connector with a specified OpenAI model (defaulting to GPT-4o).
- **Parameters**:
  - `model` (str | None): The model name. Defaults to the GPT-4o model specified in `LLMModels`.
- **Implementation Details**:
  - Retrieves the OpenAI API key from environment variables using `os.getenv`.
  - Raises a `ValueError` if the API key is not found, ensuring that the user is informed of missing credentials.
  - Calls the constructor of `BaseLLMConnector` with the API key to complete initialization.

### Method: `generate_response(self, user_prompt: str, system_prompt: str = "You are an AI assistant", temperature: float = 0.7)`

- **Purpose**: Generates a response from the GPT-4o model based on the provided prompts and temperature setting.
- **Parameters**:
  - `user_prompt` (str): The input query from the user.
  - `system_prompt` (str): Instructions to guide the AI's behavior. Defaults to "You are an AI assistant".
  - `temperature` (float): Controls the randomness of the response. A higher value yields more creative outputs, with a default of 0.7.
- **Returns**: A string containing the generated response from GPT-4o.
- **Implementation Details**:
  - Constructs a message list for the OpenAI API, including system and user prompts.
  - Calls `openai.ChatCompletion.create()` with the specified parameters to generate a response.
  - Handles potential exceptions from the OpenAI API, raising a `RuntimeError` with a descriptive message if an error occurs.

## Script Execution

The script includes a test block that executes when the script is run directly. This block demonstrates the usage of `OpenAIConnector` by generating responses to a sample user prompt, "Give me a nice romantic poem", with both a custom system prompt and the default system prompt.

- **Custom System Prompt**: "Explain concepts in simple terms."
- **Default System Prompt**: "You are an AI assistant."

The responses are printed to the console for verification.

### Important Notes

- Ensure that the OpenAI Python client library and `dotenv` are installed in your environment.
- The `.env` file must contain the appropriate API key for accessing OpenAI's services.
- The script assumes that `BaseLLMConnector` and `LLMModels` are correctly defined in their respective modules.
