import os
import time
import tiktoken
from openai import OpenAI
import random
import sys
import json
import configparser

# 调试模式开关
DEBUG_MODE = False
# 打印模型输入内容开关
PRINT_INPUT = False

# Initialize tiktoken encoder
encoding = tiktoken.get_encoding("o200k_base")

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

def process_content(provider_name, user_prompt, model, content=None, system_prompt=None, max_tokens=None, response_format=None, n=1, temperature=None):
    """
    Process content using the specified provider.
    
    Args:
        provider_name: Name of the provider to use
        user_prompt: The prompt to send to the model
        model: The model to use
        content: Optional content to append to the user prompt
        system_prompt: Optional system prompt (if not provided, no system message is sent)
        max_tokens: Optional max tokens for the response
        response_format: Optional response format specification
        n: Number of completions to generate (default 1)
        temperature: Optional temperature setting for response generation
        
    Returns:
        Dictionary containing the result, token counts, and elapsed time
    """
    # Get the OpenAI client for the specified provider
    client = get_openai_client(provider_name)
    
    # Prepare messages
    messages = []
    
    # Add system message only if provided
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Prepare user message
    user_message = user_prompt
    if content:
        user_message = f"{user_prompt}\n\n-----Content START-----\n{content}\n-----Content END-----"
    
    messages.append({"role": "user", "content": user_message})

    # 打印模型输入内容
    if PRINT_INPUT:
        print("\n=== Model Input ===")
        if system_prompt:
            print("System message:", system_prompt)
        print("\nUser message:", messages[-1]["content"])
        print("=== End Model Input ===\n")

    start_time = time.time()
    
    api_params = {
        "model": model,
        "messages": messages,
        "n": n,
    }

    # Add optional parameters if provided
    if max_tokens:
        api_params["max_tokens"] = max_tokens
    
    if temperature is not None:
        api_params["temperature"] = temperature
    
    if response_format:
        api_params["response_format"] = response_format
        if PRINT_INPUT:
            print("Response format:", json.dumps(response_format, indent=2))

    max_retries = 5
    base_delay = 30
    input_tokens = 0
    output_tokens = 0
    result = ""

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}: Sending request to {provider_name} API...", flush=True)
            completion = client.chat.completions.create(**api_params)
            
            # 只在调试模式开启时打印原始响应
            if DEBUG_MODE:
                print("Raw API response:", flush=True)
                print(completion, flush=True)
            
            if isinstance(completion, str):
                print("API returned an unexpected string response:", flush=True)
                print(completion, flush=True)
                raise ValueError("Unexpected API response format")
            
            result = completion.choices[0].message.content.strip()
            print(f"Successfully received response from {provider_name} API", flush=True)
            
            input_tokens = completion.usage.prompt_tokens
            output_tokens = completion.usage.completion_tokens
            
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

    print(f"Processing {provider_name} API completed. Input tokens: {input_tokens}, Output tokens: {output_tokens}", flush=True)

    return {
        "result": result,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "elapsed_time": elapsed_time
    }

print("openai_based_api.py module loaded", flush=True)










