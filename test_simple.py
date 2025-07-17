#!/usr/bin/env python3

import sys
import os
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the project directory to the path
sys.path.insert(0, '/home/providencia/DEVPROJECTS/gpt-draa/gpt-draa/backend')

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

# Test simple imports
try:
    from core.models import QueryLog, SystemPerformanceMetrics
    print("✅ Models imported successfully")
    
    from django.http import JsonResponse
    print("✅ Django imports working")
    
    from datetime import datetime, timedelta
    print("✅ Python imports working")
    
    # Test a simple API response
    test_data = {
        'status': 'success',
        'stats': {
            'total_queries': 5,
            'last_day': {
                'avg_response_time': 45000,
                'avg_relevance': 0.087
            }
        }
    }
    print("✅ Test data created:", test_data)
    
    print("\n🎉 Basic setup appears to be working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
