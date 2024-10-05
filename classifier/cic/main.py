import sys
import os
import argparse
from flask import Flask
from cic.blueprints.web_interface import interface_bp
from cic.blueprints.cic_api import api_bp

def create_app(src_path):
    app = Flask(__name__)

    # Configuration of SRC_PATH in the app
    app.config['SRC_PATH'] = src_path

    # Blueprint registration
    app.register_blueprint(interface_bp, url_prefix='/')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Flask application.')
    parser.add_argument('--src_path', required=True, help='Path to src folder.')
    args = parser.parse_args()

    # Create the app with user-provided SRC_PATH
    app = create_app(args.src_path)

    # Run the app
    app.run(debug=True)