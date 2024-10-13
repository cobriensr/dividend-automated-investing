# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, missing-final-newline
import os
from flask import jsonify, send_from_directory

def register_routes(app):
    @app.route('/api/data')
    def get_data():
        # Your API logic here
        return jsonify(message='Hello from Flask!')

    @app.route('/_next/<path:path>')
    def next_static(path):
        return send_from_directory(os.path.join(app.static_folder, '_next'), path)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path.startswith('api/'):
            # Let Flask handle API routes
            return app.send_static_file('404.html')
        if os.path.exists(os.path.join(app.static_folder, 'server', path)):
            return send_from_directory(os.path.join(app.static_folder, 'server'), path)
        return send_from_directory(app.static_folder, 'server/pages/index.html')