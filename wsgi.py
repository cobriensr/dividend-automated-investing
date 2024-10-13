# pylint: disable=missing-module-docstring, missing-final-newline
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
