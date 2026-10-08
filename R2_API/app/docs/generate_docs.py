import sys
import os
import ast
# Ensure the project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llms.openai_connector import OpenAIConnector

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Initialize OpenAI Connector
openai_llm = OpenAIConnector()

# Define paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))  # Gets the root directory of the project (R2_API)
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs", "documentation")  # Path where generated docs will be stored

def extract_code(file_path: str) -> str:
    """
    Reads the full content of a Python script.

    Args:
        file_path (str): Path to the Python script.

    Returns:
        str: The raw code content of the script.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_documentation_with_gpt(file_path: str) -> str:
    """
    Uses OpenAI GPT-4o to generate detailed technical documentation for a given Python script.

    Args:
        file_path (str): The original Python file path.

    Returns:
        str: The generated markdown content for documentation.
    """
    code_content = extract_code(file_path)

    # Define system prompt for OpenAI
    system_prompt = """
    You are an expert technical writer. Your task is to generate clear, detailed, and structured technical documentation 
    for the given Python script. The documentation should include:
    - A high-level overview of the script's purpose.
    - A detailed explanation of each function and its role.
    - Any important implementation details or dependencies.
    """

    # Generate response from GPT-4o
    documentation = openai_llm.generate_response(system_prompt=system_prompt, user_prompt=code_content)

    # Format into markdown
    md_content = f"# Documentation for `{os.path.basename(file_path)}`\n\n{documentation}\n"

    return md_content

def create_docs(project_root: str):
    """
    Scans project files, generates AI-generated documentation using GPT-4o, 
    and saves the results inside `docs/documentation/`, maintaining the original folder structure.
    """
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.endswith(".py") and ("docs" not in root) and (file != "__init__.py"):  # Exclude docs folder itself
                file_path = os.path.join(root, file)

                # Generate AI-powered documentation
                markdown_content = generate_documentation_with_gpt(file_path)

                # Define output path inside documentation folder
                relative_path = os.path.relpath(file_path, PROJECT_ROOT)
                doc_file_path = os.path.join(DOCS_DIR, relative_path.replace(".py", ".md"))

                # Ensure directories exist
                os.makedirs(os.path.dirname(doc_file_path), exist_ok=True)

                # Save the markdown file
                with open(doc_file_path, "w", encoding="utf-8") as md_file:
                    md_file.write(markdown_content)

                print(f" Documentation generated: {doc_file_path}")

if __name__ == "__main__":
    """
    When this script is run directly, it scans the entire project, 
    uses OpenAI GPT-4o to generate structured technical documentation, 
    and saves it inside `docs/documentation/`.
    """

    import argparse

    parser = argparse.ArgumentParser(description="Autogenerate Documentation")
    parser.add_argument("--root", type=str, default=PROJECT_ROOT, help="Project root path.")

    args = parser.parse_args()
    print(" Scanning project files for documentation...")
    create_docs(args.root)
    print("\n Documentation generation complete! Check the `docs/documentation/` folder.")
