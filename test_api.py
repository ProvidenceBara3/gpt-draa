#!/usr/bin/env python3
"""
Interactive test for the chat API
"""

import requests
import json

def test_chat():
    url = "http://localhost:8000/api/ask/"
    
    test_questions = [
        "What are the main digital inclusion challenges in Africa?",
        "How can we improve digital accessibility for people with disabilities?",
        "What role does technology play in human rights?",
        "Tell me about digital divide in Africa"
    ]
    
    print("🤖 Testing GPT-DRAA Chat System")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 40)
        
        try:
            response = requests.post(
                url,
                json={"prompt": question, "language": "en"},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response: {data['response'][:200]}...")
                print(f"📚 Context chunks: {len(data.get('context_used', []))}")
                if data.get('relevance_scores'):
                    avg_relevance = sum(data['relevance_scores']) / len(data['relevance_scores'])
                    print(f"📊 Avg relevance: {avg_relevance:.2f}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            
        print()

if __name__ == "__main__":
    test_chat()
