# core/gpt_client.py
import requests

def ask_mistral(prompt, language='en'):
    """
    Send prompt to local TinyLlama model via LM Studio
    """
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": "tinyllama-1.1b-chat-v1.0",  # Using your local TinyLlama model
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": False
    }

    try:
        response = requests.post("http://localhost:1234/v1/chat/completions", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return f"⚠️ Timeout: TinyLlama model took too long to respond. Try a shorter prompt."
    except requests.exceptions.ConnectionError:
        return f"⚠️ Connection Error: Make sure LM Studio is running on localhost:1234 with TinyLlama loaded."
    except Exception as e:
        return f"⚠️ Error communicating with TinyLlama: {e}"

