# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, missing-final-newline

import os
from flask import Flask, send_from_directory


app = Flask(__name__, static_folder='frontend/build')

# API routes
@app.route('/api/data')
def get_data():
    # Your API logic here
    return {'data': 'some data'}

# Catch all route to serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)