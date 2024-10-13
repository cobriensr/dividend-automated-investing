# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, missing-final-newline, trailing-whitespace
from flask import Flask
from flask_cors import CORS

def create_app():
    flask_app = Flask(__name__, static_folder='frontend/automated-dividend-investing/.next')
    CORS(flask_app)
    
    # Import and register routes
    from . import routes
    routes.register_routes(flask_app)
    
    return flask_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)