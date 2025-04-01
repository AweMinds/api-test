import sys
import os
import json

# Add the parent directory to the path so we can import the embedding module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding.dash_scope_embedding import process_embedding
import dashscope

def test_text_embedding():
    print("\n===== Testing Text Embedding =====")
    # Call the embedding function with "你好" as input
    response = process_embedding(
        provider_name="ALIYUN",  # Use the provider name from your .provider_env file
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        input_text="你好",
        dimensions=1024  # Optional: specify embedding dimensions
    )
    
    if response:
        # Get the embedding vector from the result
        embedding_data = response["result"].output.embeddings[0].embedding
        print(f"Embedding vector (first 10 values): {embedding_data[:10]}")
        print(f"Vector dimension: {len(embedding_data)}")
        print(f"Tokens used: {response['total_tokens']}")
        print(f"Processing time: {response['elapsed_time']:.2f} seconds")
        
        # Optional: Save the full embedding to a file
        # with open("embedding_result.json", "w") as f:
        #     json.dump(embedding_data, f)

def test_multimodal_embedding():
    print("\n===== Testing Multimodal Embedding =====")
    # Call the multimodal embedding function with text input
    response = process_embedding(
        provider_name="ALIYUN",
        model="multimodal-embedding-v1",
        input_text="通用多模态表征模型示例",
        dimensions=1024  # Optional: specify embedding dimensions
    )
    
    if response:
        # Access the embedding data based on the observed response structure
        result_obj = response["result"]
        
        # Based on the debug output, we can see the structure is accessible as a dictionary
        if hasattr(result_obj, "output") and hasattr(result_obj.output, "embeddings"):
            # Try direct attribute access
            embedding_data = result_obj.output.embeddings[0].embedding
        else:
            # Try dictionary-style access
            output = result_obj.output if hasattr(result_obj, "output") else {}
            embeddings = output.get("embeddings", [])
            
            if embeddings and len(embeddings) > 0:
                embedding_data = embeddings[0].get("embedding", []) if isinstance(embeddings[0], dict) else embeddings[0]["embedding"] if "embedding" in embeddings[0] else []
            else:
                embedding_data = []
        
        if embedding_data:
            print(f"Embedding vector (first 10 values): {embedding_data[:10]}")
            print(f"Vector dimension: {len(embedding_data)}")
            
            # Fix token count extraction
            token_count = None
            if hasattr(result_obj, "usage") and hasattr(result_obj.usage, "input_tokens"):
                token_count = result_obj.usage.input_tokens
            elif hasattr(result_obj, "usage") and isinstance(result_obj.usage, dict):
                token_count = result_obj.usage.get("input_tokens")
            
            print(f"Tokens used: {token_count or response['total_tokens']}")
            print(f"Processing time: {response['elapsed_time']:.2f} seconds")
        else:
            print("Could not find embedding data in response structure.")
            print("Raw response structure:", dir(result_obj))

def test_multimodal_with_image():
    print("\n===== Testing Multimodal Embedding with Image =====")
    # Example with both text and image
    # Replace with an actual image URL for testing
    image_url = "https://mitalinlp.oss-cn-hangzhou.aliyuncs.com/dingkun/images/1712648554702.jpg"
    
    response = process_embedding(
        provider_name="ALIYUN",
        model="multimodal-embedding-v1",
        input_text="通用多模态表征模型示例",
        image_url=image_url
    )
    
    if response:
        # Print information about each embedding
        for i, embedding_obj in enumerate(response["result"].output.embeddings):
            embedding_type = embedding_obj.type
            embedding_data = embedding_obj.embedding
            print(f"\nEmbedding {i+1} (type: {embedding_type}):")
            print(f"First 10 values: {embedding_data[:10]}")
            print(f"Vector dimension: {len(embedding_data)}")
        
        print(f"\nTokens used: {response['total_tokens']}")
        print(f"Images processed: {response.get('image_count', 0)}")
        print(f"Processing time: {response['elapsed_time']:.2f} seconds")

if __name__ == "__main__":
    # Choose which test to run
    # test_text_embedding()
    
    # Uncomment to test multimodal embedding
    test_multimodal_embedding()
    
    # Uncomment to test multimodal embedding with image
    # test_multimodal_with_image()
