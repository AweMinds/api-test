import os
import time
import random
import sys
import configparser
import dashscope
from http import HTTPStatus

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

def set_dashscope_api_key(provider_name="ALIYUN"):
    """Set DashScope API key from the provider configuration"""
    if provider_name not in PROVIDERS:
        raise ValueError(f"Provider '{provider_name}' not found. Available providers: {list(PROVIDERS.keys())}")
    
    provider = PROVIDERS[provider_name]
    dashscope.api_key = provider['api_key']

def process_embedding(provider_name, model, input_text=None, image_url=None, video_url=None, dimensions=None, output_type=None):
    """
    Generate embeddings using DashScope API.
    
    Args:
        provider_name: Name of the provider (should be ALIYUN)
        model: The embedding model to use
        input_text: Text to generate embeddings for (optional)
        image_url: URL of image to generate embeddings for (optional)
        video_url: URL of video to generate embeddings for (optional)
        dimensions: Optional embedding dimensions (not used for multimodal embeddings)
        output_type: Format for the embedding output (not used for multimodal embeddings)
        
    Returns:
        Dictionary containing the embedding data and elapsed time
    """
    # Set the API key for DashScope
    set_dashscope_api_key(provider_name)
    
    start_time = time.time()
    
    # Check if we're using the multimodal embedding model
    is_multimodal = "multimodal" in model if isinstance(model, str) else False
    
    if is_multimodal:
        # Prepare input for multimodal embedding
        if not any([input_text, image_url, video_url]):
            raise ValueError("At least one of input_text, image_url, or video_url must be provided")
        
        # For SDK, input should be a list of dictionaries
        inputs = []
        if input_text:
            inputs.append({"text": input_text})
        if image_url:
            inputs.append({"image": image_url})
        if video_url:
            inputs.append({"video": video_url})
        
        api_params = {
            "model": model,
            "input": inputs
        }
    else:
        # Legacy mode for text-only embeddings
        api_params = {
            "model": model,
            "input": input_text,
        }

        # Add dimensions parameter if provided
        if dimensions:
            api_params["dimension"] = dimensions
            
        # Add output_type parameter if provided
        if output_type:
            api_params["output_type"] = output_type

    max_retries = 5
    base_delay = 30
    result = None

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}: Sending embedding request to DashScope API...", flush=True)
            
            if is_multimodal:
                response = dashscope.MultiModalEmbedding.call(**api_params)
            else:
                response = dashscope.TextEmbedding.call(**api_params)
            
            # Only print raw response in debug mode
            if DEBUG_MODE:
                print("Raw API response:", flush=True)
                print(response, flush=True)
            
            if response.status_code == HTTPStatus.OK:
                result = response
                print("Successfully received embedding from DashScope API", flush=True)
                break
            else:
                raise Exception(f"API Error: {response}")
            
        except Exception as e:
            print(f"DashScope API encountered an error: {e}", flush=True)
            print("Error details:", flush=True)
            print(f"Type: {type(e).__name__}", flush=True)
            print(f"Arguments: {e.args}", flush=True)
            
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
        print(f"Embedding processing completed", flush=True)
        
        # Extract usage information based on model type
        if is_multimodal:
            token_count = result.usage.input_tokens if hasattr(result, 'usage') and hasattr(result.usage, 'input_tokens') else None
            prompt_tokens = token_count  # For multimodal, input_tokens is equivalent to prompt_tokens
            image_count = result.usage.image_count if hasattr(result, 'usage') and hasattr(result.usage, 'image_count') else 0
            video_duration = result.usage.duration if hasattr(result, 'usage') and hasattr(result.usage, 'duration') else 0
            
            return {
                "result": result,
                "prompt_tokens": prompt_tokens,
                "total_tokens": token_count,
                "image_count": image_count,
                "video_duration": video_duration,
                "elapsed_time": elapsed_time
            }
        else:
            token_count = result.usage.total_tokens if hasattr(result, 'usage') and hasattr(result.usage, 'total_tokens') else None
            prompt_tokens = result.usage.input_tokens if hasattr(result, 'usage') and hasattr(result.usage, 'input_tokens') else None
            
            return {
                "result": result,
                "prompt_tokens": prompt_tokens,
                "total_tokens": token_count,
                "elapsed_time": elapsed_time
            }
    
    return None

# Example usage for text-only embedding
# if __name__ == "__main__":
#     response = process_embedding(
#         provider_name="ALIYUN",
#         model=dashscope.TextEmbedding.Models.text_embedding_v3,
#         input_text="衣服的质量杠杠的，很漂亮，不枉我等了这么久啊，喜欢，以后还来这里买",
#         dimensions=1024,
#         output_type="dense&sparse"
#     )
#     
#     if response:
#         print(response["result"])

# Example usage for multimodal embedding
# if __name__ == "__main__":
#     response = process_embedding(
#         provider_name="ALIYUN",
#         model="multimodal-embedding-v1",
#         input_text="通用多模态表征模型示例",
#         image_url="https://example.com/image.jpg"
#     )
#     
#     if response:
#         print(response["result"])