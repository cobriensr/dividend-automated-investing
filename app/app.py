# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, missing-final-newline, trailing-whitespace, line-too-long
import os
import json
import logging
from pathlib import Path
from flask import Flask, send_from_directory
from flask_cors import CORS
from .routes import register_routes

# schema directory
SCHEMA_DIR = Path(__file__).parent / 'schemas'

with open(SCHEMA_DIR / 'api_schemas.json', encoding='utf-8') as f:
    api_schemas = json.load(f)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the absolute path to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_app():
    logger.info("Starting create_app()")
    try:
        flask_app = Flask(
            __name__,
            static_folder=os.path.join(
                project_root, "frontend", "automated-dividend-investing", "out"
            ),
        )
        logger.debug("Flask app created")

        CORS(flask_app)
        logger.debug("CORS initialized")

        # Configure upload folder
        flask_app.config["UPLOAD_FOLDER"] = os.path.join(project_root, "uploads")
        logger.debug("Upload folder set to: %s", flask_app.config["UPLOAD_FOLDER"])

        try:
            os.makedirs(flask_app.config["UPLOAD_FOLDER"], exist_ok=True)
            logger.info("Upload folder created/verified: %s", flask_app.config["UPLOAD_FOLDER"])
        except OSError as e:
            logger.error("Failed to create upload folder: %s", e, exc_info=True)

        try:
            register_routes(flask_app)
            logger.info("Routes registered successfully")
        except ImportError as e:
            logger.error("Failed to register routes: %s", e, exc_info=True)

        @flask_app.route("/", defaults={"path": ""})
        @flask_app.route("/<path:path>")
        def serve_frontend(path):
            logger.debug("Serving frontend for path: %s", path)
            if path != "" and os.path.exists(os.path.join(flask_app.static_folder, path)):
                return send_from_directory(flask_app.static_folder, path)
            return send_from_directory(flask_app.static_folder, "index.html")

        logger.info("Finished create_app()")
        return flask_app
    except (OSError, ImportError) as e:
        logger.critical("Failed to create app: %s", e, exc_info=True)
        raise

if __name__ == "__main__":
    app = create_app()
    logger.info("Starting Flask development server")
    app.run(host="0.0.0.0", port=5001)