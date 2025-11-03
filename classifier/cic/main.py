import sys
import os
import argparse
from flask import Flask
from cic.blueprints.web_interface import interface_bp
from cic.blueprints.cic_api import api_bp

def create_app(src_path, prefix = "/cic"):
    app = Flask(__name__, static_url_path=prefix+'/static', static_folder="static")

    # Do not sort JSON keys; preserve insertion order for frontend
    app.config["JSON_SORT_KEYS"] = False           # Flask ≤ 2.2
    try:
        app.json.sort_keys = False                 # Flask 2.3+
    except Exception:
        pass

    # Configuration of SRC_PATH in the app
    app.config['SRC_PATH'] = src_path

    # Blueprint registration
    app.register_blueprint(interface_bp, url_prefix=prefix+'/')
    app.register_blueprint(api_bp, url_prefix=prefix+'/api')

    return app


# Create app instance for Gunicorn (uses environment variables)
src_path = os.getenv('SRC_PATH', '/app/classifier/cic/src')
prefix = os.getenv('URL_PREFIX', '/cic')
app = create_app(src_path, prefix)


if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Flask application.')
    parser.add_argument('--src_path', required=True, help='Path to src folder.')
    parser.add_argument('--prefix', required=True, help='Aplication Prefix')
    args = parser.parse_args()
    
    # Override with CLI args if provided
    if args.src_path or args.prefix:
        app = create_app(
            args.src_path or src_path,
            args.prefix or prefix
        )
    
    # Run with Flask dev server
    app.run(host='0.0.0.0', port=5000, debug=False)
