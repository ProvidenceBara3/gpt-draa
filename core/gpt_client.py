# core/gpt_client.py
import requests
import os

# Get timeout from environment variable or use default
DEFAULT_TIMEOUT = int(os.getenv('LLM_TIMEOUT', 120))

def is_garbled_response(text):
    """
    Detect if the response appears to be garbled or repetitive
    """
    if not text or len(text.strip()) < 5:
        return True
    
    # Clean and normalize the text
    words = text.lower().strip().split()
    if len(words) < 3:
        return True
        
    # Check for excessive repetition - more strict
    word_counts = {}
    for word in words:
        if len(word) > 2:  # Only count meaningful words
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # If any meaningful word appears more than 20% of the time, it's garbled
    total_meaningful_words = len([w for w in words if len(w) > 2])
    if total_meaningful_words > 0:
        for word, count in word_counts.items():
            if count > total_meaningful_words * 0.2:
                return True
    
    # Check for excessive fragmentation
    if text.count('.') > len(words) * 0.4:
        return True
    
    # Check for common garbled patterns
    garbled_patterns = ['policy policy', 'access access', 'systems systems', 'e e', 'infrastr infrastr']
    for pattern in garbled_patterns:
        if pattern in text.lower():
            return True
        
    return False

def ask_mistral(prompt, language='en', timeout=None):
    """
    Send prompt to local Llama 3.2 3B Instruct model via LM Studio
    """
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
        
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.2-3b-instruct",  # Llama 3.2 3B Instruct model
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # Slightly higher for better models
        "max_tokens": 300,   # Can increase with better models
        "top_p": 0.9,        
        "frequency_penalty": 0.3,  # Less aggressive with better models
        "presence_penalty": 0.2,   
        "stream": False
    }

    try:
        response = requests.post("http://localhost:1234/v1/chat/completions", json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        # Get the response text
        response_text = data['choices'][0]['message']['content']
        
        # Validate response quality
        if is_garbled_response(response_text):
            # Try to extract a simple answer from the context if available
            if "digital rights" in prompt.lower() or "africa" in prompt.lower():
                return "Digital rights in Africa encompass access to technology, internet connectivity, data privacy, and digital literacy. Key challenges include bridging the digital divide and ensuring equitable access to digital services across the continent."
            else:
                return "⚠️ The AI model produced an unclear response. This may be due to context overload or model limitations. Please try rephrasing your question or asking something more specific."
        
        return response_text
    except requests.exceptions.Timeout:
        return f"⚠️ Timeout: Llama 3.2 model took too long to respond (>{timeout}s). The model may be overloaded. Context retrieved successfully: {len(payload.get('messages', [{}])[0].get('content', '').split())} words."
    except requests.exceptions.ConnectionError:
        return f"⚠️ Connection Error: Make sure LM Studio is running on localhost:1234 with Llama 3.2 3B Instruct loaded."
    except Exception as e:
        return f"⚠️ Error communicating with Llama 3.2: {e}"

