# core/gpt_client.py
import requests

def ask_mistral(prompt, language='en'):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral",  # or the exact model name shown in LM Studio
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("http://localhost:1234/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Error: {e}"

