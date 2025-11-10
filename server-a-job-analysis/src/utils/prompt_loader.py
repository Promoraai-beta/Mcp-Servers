"""
Prompt loader utility for loading prompt templates from text files.
"""

import os
# No typing imports needed for basic string operations


def load_prompt(filename: str) -> str:
    """
    Load a prompt template from a text file.
    
    Args:
        filename (str): The name of the prompt file (e.g., 'validate_job_link.txt')
        
    Returns:
        str: The content of the prompt file as a string
        
    Raises:
        FileNotFoundError: If the prompt file is not found
        IOError: If there's an error reading the file
    """
    # Get the directory of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Navigate to the prompts directory
    prompts_dir = os.path.join(current_dir, '..', 'prompts')
    prompt_path = os.path.join(prompts_dir, filename)
    
    # Check if file exists
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except IOError as e:
        raise IOError(f"Error reading prompt file {filename}: {str(e)}")


def load_prompt_with_placeholder(filename: str, placeholder: str, replacement: str) -> str:
    """
    Load a prompt template and replace a placeholder with actual content.
    
    Args:
        filename (str): The name of the prompt file
        placeholder (str): The placeholder to replace (e.g., '{{html_content}}')
        replacement (str): The content to replace the placeholder with
        
    Returns:
        str: The prompt with the placeholder replaced
    """
    prompt_template = load_prompt(filename)
    return prompt_template.replace(placeholder, replacement)
