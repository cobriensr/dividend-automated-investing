# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, missing-final-newline, trailing-whitespace
import os
from flask import jsonify, send_from_directory, current_app

def register_routes(app):
    @app.route('/api/data')
    def get_data():
        # Your API logic here
        return jsonify(message='Hello from Flask!')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_next(path):
        print(f"Requested path: {path}")
        print(f"Full path: {os.path.join(current_app.static_folder, path)}")
        if path.startswith('api/'):
            # Let Flask handle API routes
            return app.send_static_file('404.html')
        
        # Try to serve the file directly
        if path != "" and os.path.exists(os.path.join(current_app.static_folder, path)):
            return send_from_directory(current_app.static_folder, path)
        
        # For app router, we need to check for HTML files
        if path == "" or not "." in path:
            if os.path.exists(os.path.join(current_app.static_folder, f"{path}.html")):
                return send_from_directory(current_app.static_folder, f"{path}.html")
            else:
                return send_from_directory(current_app.static_folder, "index.html")
        
        # If nothing matches, return 404
        return app.send_static_file('404.html')

    # This line is optional, but can be helpful for debugging
    if __name__ == '__main__':
        print("Routes module loaded successfully")