import sys
import os
import argparse
from flask import Flask
from cic.blueprints.web_interface import interface_bp
from cic.blueprints.cic_api import api_bp

def create_app(src_path, prefix = "/cic"):
    app = Flask(__name__, static_url_path=prefix+'/static', static_folder="static")

    # Configuration of SRC_PATH in the app
    app.config['SRC_PATH'] = src_path

    # Blueprint registration
    app.register_blueprint(interface_bp, url_prefix=prefix+'/')
    app.register_blueprint(api_bp, url_prefix=prefix+'/api')

    return app

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Flask application.')
    parser.add_argument('--src_path', required=True, help='Path to src folder.')
    parser.add_argument('--prefix', required=True, help='Aplication Prefix')
    args = parser.parse_args()
    
    # Create the app with user-provided SRC_PATH
    app = create_app(args.src_path, args.prefix)
    
    # Get host and port from environment or use defaults
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Run the app
    app.run(debug=debug, host=host, port=port)
