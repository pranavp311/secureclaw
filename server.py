"""Web UI entry point using the app/ package (interactive dot background)."""
import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SecureClaw Web UI")
    parser.add_argument("--port", type=int, default=5001, help="Port (default: 5001)")
    args = parser.parse_args()

    try:
        from app import create_web_app
    except ImportError:
        print("Flask is required for the web UI. Install with: pip install flask")
        sys.exit(1)

    app = create_web_app()
    print(f"\n  SecureClaw running at http://localhost:{args.port}\n")
    app.run(host="0.0.0.0", port=args.port, debug=False)
