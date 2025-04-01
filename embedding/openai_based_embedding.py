import os
import time
import random
import sys
import configparser
from openai import OpenAI

# 调试模式开关
DEBUG_MODE = False

# Load providers from .provider_env file
def load_providers():
    providers = {}
    config = configparser.ConfigParser()
    
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.provider_env')
        config.read(config_path)
        
        for provider in config.sections():
            providers[provider] = {
                'api_key': config[provider]['api_key'],
                'base_url': config[provider]['base_url']
            }
        
        if not providers:
            print("Warning: No providers found in .provider_env file", flush=True)
    except Exception as e:
        print(f"Error loading providers: {e}", flush=True)
    
    return providers

PROVIDERS = load_providers()

def get_openai_client(provider_name):
    """Get OpenAI client for the specified provider"""
    if provider_name not in PROVIDERS:
        raise ValueError(f"Provider '{provider_name}' not found. Available providers: {list(PROVIDERS.keys())}")
    
    provider = PROVIDERS[provider_name]
    return OpenAI(
        api_key=provider['api_key'],
        base_url=provider['base_url']
    )

def process_embedding(provider_name, model, input_text, dimensions=None, encoding_format="float"):
    """
    Generate embeddings using the specified provider.
    
    Args:
        provider_name: Name of the provider to use
        model: The embedding model to use
        input_text: Text to generate embeddings for
        dimensions: Optional embedding dimensions (supported by models like text-embedding-v3)
        encoding_format: Format for the embedding output (default "float")
        
    Returns:
        Dictionary containing the embedding data, token counts, and elapsed time
    """
    # Get the OpenAI client for the specified provider
    client = get_openai_client(provider_name)
    
    start_time = time.time()
    
    api_params = {
        "model": model,
        "input": input_text,
        "encoding_format": encoding_format
    }

    # Add dimensions parameter if provided
    if dimensions:
        api_params["dimensions"] = dimensions

    max_retries = 5
    base_delay = 30
    result = None

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}: Sending embedding request to {provider_name} API...", flush=True)
            completion = client.embeddings.create(**api_params)
            
            # Only print raw response in debug mode
            if DEBUG_MODE:
                print("Raw API response:", flush=True)
                print(completion, flush=True)
            
            result = completion
            print(f"Successfully received embedding from {provider_name} API", flush=True)
            break
            
        except Exception as e:
            print(f"{provider_name} API encountered an error: {e}", flush=True)
            print("Error details:", flush=True)
            print(f"Type: {type(e).__name__}", flush=True)
            print(f"Arguments: {e.args}", flush=True)
            
            if hasattr(e, 'response'):
                print("API Response:", flush=True)
                print(f"Status: {e.response.status_code}", flush=True)
                print(f"Headers: {e.response.headers}", flush=True)
                print(f"Content: {e.response.text}", flush=True)
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 10)
                print(f"Retrying in {delay:.2f} seconds...", flush=True)
                sys.stdout.flush()
                time.sleep(delay)
            else:
                print(f"Maximum retry attempts reached.", flush=True)
                raise

    end_time = time.time()
    elapsed_time = end_time - start_time

    if result:
        print(f"Embedding processing completed with {result.usage.prompt_tokens} tokens", flush=True)
        return {
            "result": result,
            "prompt_tokens": result.usage.prompt_tokens,
            "total_tokens": result.usage.total_tokens,
            "elapsed_time": elapsed_time
        }
    
    return None

# # Example usage
# if __name__ == "__main__":
#     response = process_embedding(
#         provider_name="ALIYUN",
#         model="text-embedding-v3",
#         input_text="衣服的质量杠杠的，很漂亮，不枉我等了这么久啊，喜欢，以后还来这里买",
#         dimensions=1024
#     )
    
#     if response:
#         print(response["result"].model_dump_json())