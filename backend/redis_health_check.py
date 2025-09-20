#!/usr/bin/env python3
"""
Simple Redis health check script.
"""
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.services.redis_client import RedisClient
    print("✓ Successfully imported Redis client")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def main():
    """Run Redis health check."""
    print("Redis Health Check")
    print("-" * 30)
    
    try:
        # Create Redis client
        client = RedisClient(host="localhost", port=6379, db=15)
        print(f"✓ Redis client created for {client.host}:{client.port}")
        
        # Perform health check
        is_healthy = client.health_check()
        
        if is_healthy:
            print("✓ Redis is healthy and responding to ping")
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = f"test_value_{datetime.utcnow().isoformat()}"
            
            # Set a test value
            client.client.set(test_key, test_value, ex=10)  # 10 second TTL
            print("✓ Successfully set test value")
            
            # Get the test value
            retrieved_value = client.client.get(test_key)
            if retrieved_value == test_value:
                print("✓ Successfully retrieved test value")
            else:
                print(f"✗ Retrieved value mismatch: expected {test_value}, got {retrieved_value}")
                return False
            
            # Clean up
            client.client.delete(test_key)
            print("✓ Successfully cleaned up test data")
            
            print("-" * 30)
            print("✓ Redis health check passed!")
            return True
            
        else:
            print("✗ Redis health check failed")
            print("  Make sure Redis is running on localhost:6379")
            return False
            
    except Exception as e:
        print(f"✗ Redis health check failed with error: {e}")
        print("  Make sure Redis is running and accessible")
        return False
    
    finally:
        try:
            client.close()
            print("✓ Redis connection closed")
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)