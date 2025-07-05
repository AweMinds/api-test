import sys
import os

# Add the parent directory to sys.path to import the LLM module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.openai_based_api import process_content

def main():
    provider_name = "YUNWU-Dev"
    model = "gpt-4.1-2025-04-14"
    user_prompt = "strawberry中有几个r？"
    
    # Call the API with default settings
    response = process_content(
        provider_name=provider_name,
        user_prompt=user_prompt,
        model=model
    )
    
    # Print the result
    print("\nAPI Response:")
    print(response)

if __name__ == "__main__":
    main()
