"""
Run the Contract Risk Analysis System.

Usage:
    python run.py              # Start the server
    python run.py --port 8000  # Custom port
    python run.py --init-db    # Initialize database only
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Contract Risk Analysis System")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--init-db", action="store_true", help="Initialize database only")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Ensure data directories exist
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/templates", exist_ok=True)

    if args.init_db:
        from src.db.database import init_db
        init_db()
        print("Database initialized successfully.")
        return

    import uvicorn
    print(f"Starting Contract Risk Analysis System on http://{args.host}:{args.port}")
    print(f"Dashboard: http://localhost:{args.port}/static/index.html")
    print(f"API docs:  http://localhost:{args.port}/docs")
    uvicorn.run(
        "src.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
