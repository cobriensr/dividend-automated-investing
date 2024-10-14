# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, missing-final-newline, trailing-whitespace, line-too-long
import os
from io import BytesIO
import pandas as pd
from flask import jsonify, send_from_directory, current_app, request
from werkzeug.utils import secure_filename


def register_routes(app):
    @app.route("/api/data")
    def get_data():
        # Your existing API logic here
        return jsonify(message="Hello from Flask!")

    @app.route("/api/upload", methods=["POST"])
    def upload_file():
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file:
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit(".", 1)[1].lower()

            if file_extension not in ["csv", "xls", "xlsx"]:
                return (
                    jsonify(
                        {
                            "error": "Unsupported file format. Please upload a CSV, XLS, or XLSX file."
                        }
                    ),
                    400,
                )

            try:
                if file_extension == "csv":
                    df = pd.read_csv(BytesIO(file.read()))
                else:  # xls or xlsx
                    xls = pd.ExcelFile(BytesIO(file.read()))
                    if "All" in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name="All")
                    else:
                        return (
                            jsonify(
                                {
                                    "error": "The Excel file does not contain a sheet named 'All'."
                                }
                            ),
                            400,
                        )

                # Here you can perform any operations on the DataFrame if needed
                print(f"DataFrame shape: {df.shape}")
                print(f"DataFrame head:\n{df.head()}")

                return jsonify(
                    {
                        "message": f"File '{filename}' received and loaded successfully.",
                        "rows": df.shape[0],
                        "columns": df.shape[1],
                    }
                )

            except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as e:
                return (
                    jsonify(
                        {
                            "error": f"An error occurred while processing the file: {str(e)}"
                        }
                    ),
                    500,
                )

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_next(path):
        print(f"Requested path: {path}")
        print(f"Full path: {os.path.join(current_app.static_folder, path)}")

        if path.startswith("api/"):
            # Let Flask handle API routes
            return app.send_static_file("404.html")

        # Try to serve the file directly
        if path != "" and os.path.exists(os.path.join(current_app.static_folder, path)):
            return send_from_directory(current_app.static_folder, path)

        # For app router, we need to check for HTML files
        if path == "" or "." not in path:
            if os.path.exists(os.path.join(current_app.static_folder, f"{path}.html")):
                return send_from_directory(current_app.static_folder, f"{path}.html")
            else:
                return send_from_directory(current_app.static_folder, "index.html")

        # If nothing matches, return 404
        return app.send_static_file("404.html")


# This line is optional, but can be helpful for debugging
if __name__ == "__main__":
    print("Routes module loaded successfully")
