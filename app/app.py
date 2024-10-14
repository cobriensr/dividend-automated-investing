# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, missing-final-newline, trailing-whitespace, line-too-long
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from .routes import register_routes

# Get the absolute path to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_app():
    flask_app = Flask(__name__, static_folder=os.path.join(project_root, 'frontend', 'automated-dividend-investing', 'out'))
    CORS(flask_app)
    
    # Configure upload folder
    flask_app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
    if not os.path.exists(flask_app.config['UPLOAD_FOLDER']):
        os.makedirs(flask_app.config['UPLOAD_FOLDER'])
    
    register_routes(flask_app)
    
    @flask_app.route('/', defaults={'path': ''})
    @flask_app.route('/<path:path>')
    def serve_frontend(path):
        if path != "" and os.path.exists(os.path.join(flask_app.static_folder, path)):
            return send_from_directory(flask_app.static_folder, path)
        else:
            return send_from_directory(flask_app.static_folder, 'index.html')
    
    return flask_app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001)