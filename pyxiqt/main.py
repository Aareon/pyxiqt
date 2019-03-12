import sys
import json
import os
import subprocess
import threading
from pathlib import Path

from PyQt5.Qt import *


class XiWorker(object):

    def __init__(self, listener):
        self.listener = listener
        self.thread = threading.Thread(target=self.runit)

    def start(self):
        if hasattr(self, "thread"):
            self.thread.start()

    def join(self):
        if hasattr(self, "thread"):
            self.thread.join()

    def runit(self):
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        cwd = Path(__file__)
        cwd = cwd.parent if cwd.is_file() else cwd
        cwd = str((cwd / "../bin").resolve())

        self.process = subprocess.Popen(
            ["xi-core.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            startupinfo=startupinfo,
            shell=True,
            cwd=cwd
        )

        while True:
            data = os.read(self.process.stdout.fileno(), 2**15)

            if len(data) > 0:
                if self.listener:
                    self.listener.on_data(self, data)
            else:
                self.process.stdout.close()
                self.process.wait()
                break

        return_code = self.process.returncode
        self.listener.on_data(self, f"return_code: {return_code}")


class XiListener(QObject):

    line_read = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = ""
        self.encoding = "utf8"

    def on_data(self, async_process, data):
        try:
            characters = data.decode(self.encoding)
        except Exception as e:
            characters = "[Decode error - output not " + self.encoding + "]\n"

        characters = characters.replace('\r\n', '\n').replace('\r', '\n')
        self.buffer += characters

        while True:
            try:
                index = self.buffer.index("\n")
            except Exception as e:
                break

            line = self.buffer[:index]
            self.buffer = self.buffer[index + 1:]
            self.line_read.emit(line)


class XiServer(QObject):

    started = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listener = XiListener()
        self.worker = XiWorker(self.listener)
        self.worker.start()
        self.listener.line_read.connect(self.on_line_read)

    def on_line_read(self, l):
        print(l)
        if l.endswith("xi-core.log"):
            self.started.emit()

    def send(self, data):
        request = json.dumps(data).encode("utf-8")
        print(request)
        process = self.worker.process
        process.stdin.write(request)
        res = process.communicate()[0]
        print(res)


class App(QApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xi = XiServer()
        self.xi.started.connect(self.on_started)

    def on_started(self):
        print("Xi Server listening...")
        self.xi.send({
            "method": "new_view",
            "file_path": __file__
        })


if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit(app.exec_())
