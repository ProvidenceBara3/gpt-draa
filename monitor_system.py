#!/usr/bin/env python3
"""
Monitoring and evaluation script for GPT-DRAA performance
"""

import requests
import json
import time
from datetime import datetime

class SystemMonitor:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        
    def test_system_performance(self):
        """Run a series of tests to evaluate system performance"""
        
        test_queries = [
            {"prompt": "What are digital inclusion challenges in Africa?", "language": "en", "expected_context": True},
            {"prompt": "How can we improve accessibility for disabled people?", "language": "en", "expected_context": True},
            {"prompt": "Tell me about CIPESA", "language": "en", "expected_context": True},
            {"prompt": "What is digital divide?", "language": "en", "expected_context": True},
            {"prompt": "Quels sont les défis numériques en Afrique?", "language": "fr", "expected_context": True},
            {"prompt": "What is quantum computing?", "language": "en", "expected_context": False},  # Should have low relevance
        ]
        
        print("🔍 Running System Performance Tests")
        print("=" * 50)
        
        results = []
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {test['prompt'][:50]}...")
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/ask/",
                    json=test,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = {
                        "test_id": i,
                        "query": test['prompt'],
                        "language": test['language'],
                        "response_time_ms": response_time,
                        "context_chunks": len(data.get('context_used', [])),
                        "relevance_scores": data.get('relevance_scores', []),
                        "avg_relevance": sum(data.get('relevance_scores', [])) / len(data.get('relevance_scores', [])) if data.get('relevance_scores') else 0,
                        "expected_context": test['expected_context'],
                        "success": True
                    }
                    
                    print(f"✅ Success - {response_time:.0f}ms")
                    print(f"📚 Context chunks: {result['context_chunks']}")
                    print(f"📊 Avg relevance: {result['avg_relevance']:.3f}")
                    
                    if test['expected_context'] and result['context_chunks'] == 0:
                        print("⚠️  Warning: Expected context but none found")
                    elif not test['expected_context'] and result['avg_relevance'] > 0.1:
                        print("⚠️  Warning: Unexpected high relevance for off-topic query")
                        
                else:
                    result = {
                        "test_id": i,
                        "query": test['prompt'],
                        "error": f"HTTP {response.status_code}",
                        "success": False
                    }
                    print(f"❌ Failed - HTTP {response.status_code}")
                    
                results.append(result)
                
            except Exception as e:
                result = {
                    "test_id": i,
                    "query": test['prompt'],
                    "error": str(e),
                    "success": False
                }
                results.append(result)
                print(f"❌ Exception: {e}")
                
            time.sleep(1)  # Rate limiting
            
        return results
    
    def get_system_stats(self):
        """Get current system statistics"""
        try:
            response = requests.get(f"{self.base_url}/monitoring/stats/", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_monitoring_dashboard(self):
        """Get monitoring dashboard data"""
        try:
            response = requests.get(f"{self.base_url}/monitoring/dashboard/", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def generate_performance_report(self, results):
        """Generate a performance evaluation report"""
        
        successful_tests = [r for r in results if r.get('success')]
        failed_tests = [r for r in results if not r.get('success')]
        
        if successful_tests:
            avg_response_time = sum(r['response_time_ms'] for r in successful_tests) / len(successful_tests)
            avg_relevance = sum(r['avg_relevance'] for r in successful_tests) / len(successful_tests)
            avg_context_chunks = sum(r['context_chunks'] for r in successful_tests) / len(successful_tests)
        else:
            avg_response_time = avg_relevance = avg_context_chunks = 0
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE EVALUATION REPORT")
        print("="*60)
        print(f"🕐 Test Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed Tests: {len(failed_tests)}")
        
        if successful_tests:
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   ⏱️  Average Response Time: {avg_response_time:.0f} ms")
            print(f"   📊 Average Relevance Score: {avg_relevance:.3f}")
            print(f"   📚 Average Context Chunks: {avg_context_chunks:.1f}")
            
            # Performance thresholds
            print(f"\n🎯 PERFORMANCE EVALUATION:")
            if avg_response_time < 5000:
                print("   ✅ Response time: EXCELLENT (< 5s)")
            elif avg_response_time < 10000:
                print("   🟡 Response time: GOOD (< 10s)")
            else:
                print("   🔴 Response time: NEEDS IMPROVEMENT (> 10s)")
                
            if avg_relevance > 0.05:
                print("   ✅ Relevance scores: GOOD (> 0.05)")
            elif avg_relevance > 0.03:
                print("   🟡 Relevance scores: FAIR (> 0.03)")
            else:
                print("   🔴 Relevance scores: NEEDS IMPROVEMENT (< 0.03)")
                
            if avg_context_chunks >= 3:
                print("   ✅ Context retrieval: EXCELLENT (≥ 3 chunks)")
            elif avg_context_chunks >= 1:
                print("   🟡 Context retrieval: ADEQUATE (≥ 1 chunk)")
            else:
                print("   🔴 Context retrieval: POOR (< 1 chunk)")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - Test {test['test_id']}: {test.get('error', 'Unknown error')}")
        
        print("\n" + "="*60)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "avg_response_time_ms": avg_response_time,
            "avg_relevance_score": avg_relevance,
            "avg_context_chunks": avg_context_chunks,
            "performance_grade": self._calculate_grade(avg_response_time, avg_relevance, avg_context_chunks)
        }
    
    def _calculate_grade(self, response_time, relevance, context_chunks):
        """Calculate overall performance grade"""
        score = 0
        
        # Response time score (40% weight)
        if response_time < 5000:
            score += 40
        elif response_time < 10000:
            score += 25
        else:
            score += 10
            
        # Relevance score (40% weight)
        if relevance > 0.05:
            score += 40
        elif relevance > 0.03:
            score += 25
        else:
            score += 10
            
        # Context retrieval score (20% weight)
        if context_chunks >= 3:
            score += 20
        elif context_chunks >= 1:
            score += 15
        else:
            score += 5
            
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Fair)"
        elif score >= 60:
            return "D (Poor)"
        else:
            return "F (Needs Major Improvement)"

def main():
    monitor = SystemMonitor()
    
    print("🚀 Starting GPT-DRAA System Monitoring")
    print("🔗 API Base URL: http://localhost:8000/api")
    
    # Run performance tests
    results = monitor.test_system_performance()
    
    # Generate report
    report = monitor.generate_performance_report(results)
    
    # Get system stats
    print("\n📈 Getting System Statistics...")
    stats = monitor.get_system_stats()
    if 'stats' in stats:
        print(f"📊 Total Queries: {stats['stats']['total_queries']}")
        languages_str = ', '.join([f"{lang['language']}({lang['count']})" for lang in stats['stats']['languages']])
        print(f"🌍 Languages: {languages_str}")
    
    print(f"\n🎓 Overall Performance Grade: {report['performance_grade']}")
    print("\n✨ Monitoring complete!")

if __name__ == "__main__":
    main()
