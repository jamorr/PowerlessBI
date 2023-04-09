import os
# from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DirectoryHandler(FileSystemEventHandler):

    def __init__(self, dir_path, on_subdirs_update=None):
        super().__init__()
        self.dir_path = dir_path
        self.on_subdirs_update = on_subdirs_update
        self.update_subdirs()

    def on_created(self, event):
        if event.is_directory:
            self.update_subdirs()

    def on_deleted(self, event):
        if event.is_directory:
            self.update_subdirs()

    def on_modified(self, event):
        if event.is_directory:
            self.update_subdirs()

    def on_moved(self, event):
        if event.is_directory:
            self.update_subdirs()

    def update_subdirs(self):
        self.subdirs = [
            os.path.join(self.dir_path, name)
            for name in os.listdir(self.dir_path)
            if os.path.isdir(os.path.join(self.dir_path, name))
        ]
        if self.on_subdirs_update:
            self.on_subdirs_update()

dir_path = '/path/to/directory'
handler = DirectoryHandler(dir_path)
# observer = Observer()
# observer.schedule(handler, dir_path, recursive=True)
# observer.start()

# try:
#     while True:
#         pass
# except KeyboardInterrupt:
#     observer.stop()
# observer.join()
