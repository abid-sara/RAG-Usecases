#!/usr/bin/env python
"""
OpenWebUI LLM API Client
For use with the deepseek-r1:14b model via the Open WebUI API
"""

import requests
import json
import argparse

def query_llm(base_url, jwt_token, prompt, model="deepseek-r1:14b", temperature=0.7, max_tokens=500):
    """Send a prompt to the LLM API and return the response"""
    url = f"{base_url}/api/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        response_data = response.json()
        
        # Extract the content from the response
        if ("choices" in response_data and 
            len(response_data["choices"]) > 0 and 
            "message" in response_data["choices"][0] and
            "content" in response_data["choices"][0]["message"]):
            
            content = response_data["choices"][0]["message"]["content"]
            return True, content
        else:
            return False, f"Unexpected response format: {json.dumps(response_data, indent=2)}"
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        if 'response' in locals():
            if hasattr(response, 'status_code'):
                error_message += f"\nStatus code: {response.status_code}"
            if hasattr(response, 'text'):
                error_message += f"\nResponse: {response.text[:200]}..."
        return False, error_message

def main():
    parser = argparse.ArgumentParser(description='Query an LLM via Open WebUI API')
    parser.add_argument('--url', type=str, default="http://10.80.10.210:8080", 
                        help='Base URL of the API')
    parser.add_argument('--token', type=str, 
                        help='JWT token for authentication')
    parser.add_argument('--model', type=str, default="deepseek-r1:14b",
                        help='Model to use for completion')
    parser.add_argument('--temperature', type=float, default=0.7,
                        help='Temperature for sampling (0.0-1.0)')
    parser.add_argument('--max-tokens', type=int, default=500,
                        help='Maximum tokens to generate')
    parser.add_argument('prompt', type=str, nargs='?',
                        help='Prompt to send to the LLM')
    
    args = parser.parse_args()
    
    # Get token from args or input
    token = args.token
    if not token:
        token = input("Enter JWT token: ")
    
    # Get prompt from args or input
    prompt = args.prompt
    if not prompt:
        prompt = input("Enter your prompt: ")
    
    success, result = query_llm(
        args.url, 
        token, 
        prompt,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    
    if success:
        print("\n--- LLM Response ---")
        print(result)
    else:
        print("\n--- Error ---")
        print(result)

if __name__ == "__main__":
    main()
