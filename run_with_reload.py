# pylint: disable=missing-module-docstring, missing-function-docstring, trailing-whitespace, missing-final-newline, invalid-name, missing-class-docstring

import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_server()

    def on_any_event(self, event):
        if event.src_path.endswith('.py'):  # Only react to Python file changes
            print(f"Change detected in {event.src_path}. Restarting server...")
            self.restart_server()

    def restart_server(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        self.process = subprocess.Popen([
            'gunicorn',
            '--config', 'gunicorn.conf.py',
            'wsgi:app'
        ])

if __name__ == "__main__":
    path = '.'  # Watch the current directory
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()