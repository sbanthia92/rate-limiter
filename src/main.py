#!/usr/bin/env python3
"""
Rate Limiter Service
A high-performance rate limiting service with HTTP API.
"""

import sys

def check_dependencies():
    """Check if required dependencies are installed."""
    dependencies = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic')
    ]
    
    missing = []
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✓ {name} is installed")
        except ImportError:
            print(f"✗ {name} is not installed")
            missing.append(module)
    
    if missing:
        print(f"\nInstall missing dependencies: pip install {' '.join(missing)}")
        return False
    return True

def main():
    """Main entry point for the rate limiter service."""
    print("Rate Limiter Service")
    print("===================")
    
    if not check_dependencies():
        sys.exit(1)
    
    print("\nStarting rate limiter service...")
    print("Default algorithm: Sliding Window with configuration: 100 requests per 60 seconds")
    print("\nAPI endpoints:")
    print("  POST /api/v1/ratelimit - Check rate limits")
    print("  POST /api/v1/configure - Update configuration")
    print("\nService will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the service\n")
    
    try:
        import uvicorn
        from api import app
        uvicorn.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            log_level="error",
            workers=1,
            loop="asyncio",
            http="h11",
            access_log=False,
            backlog=2048,
            limit_concurrency=1000,
            limit_max_requests=10000
        )
    except KeyboardInterrupt:
        print("\nShutting down rate limiter service...")
    except Exception as e:
        print(f"Error starting service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
