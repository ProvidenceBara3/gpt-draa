#!/usr/bin/env python3
"""
Simple chat client to test the ask_view endpoint
"""

import requests
import json

def chat_with_api(base_url="http://localhost:8000"):
    print("🤖 GPT-DRAA Chat Client")
    print("=" * 50)
    print("Available languages: en (English), fr (French), sw (Swahili), am (Amharic)")
    print("Type 'quit' to exit\n")
    
    # Get language preference
    language = input("Choose language [en]: ").strip() or "en"
    if language not in ['en', 'fr', 'sw', 'am']:
        language = 'en'
    
    while True:
        # Get user input
        user_prompt = input(f"\n[{language}] Your question: ").strip()
        
        if user_prompt.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not user_prompt:
            continue
            
        # Make API request
        try:
            response = requests.post(
                f"{base_url}/api/ask/",
                json={
                    "prompt": user_prompt,
                    "language": language
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Display response
                print(f"\n🤖 Response:")
                print("-" * 40)
                print(data["response"])
                
                # Show context info
                if data.get("context_used"):
                    print(f"\n📚 Context used: {len(data['context_used'])} chunks")
                    if data.get("relevance_scores"):
                        avg_relevance = sum(data["relevance_scores"]) / len(data["relevance_scores"])
                        print(f"📊 Average relevance: {avg_relevance:.2f}")
                else:
                    print("\n📚 No specific context found")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error. Is the Django server running on localhost:8000?")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    chat_with_api()
