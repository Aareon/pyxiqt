from PyQt5.Qt import *
import sys
from pathlib import Path


class Xi(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def start(self):
        root_path = Path(__file__)
        root_path = root_path.parent if root_path.is_file() else root_path

        self.process = QProcess()
        self.process.readyRead.connect(self.on_ready_read)
        self.process.readyReadStandardOutput.connect(self.on_ready_read_standard_output)
        self.process.readyReadStandardError.connect(self.on_ready_read_standard_error)
        self.process.errorOccurred.connect(self.on_error_ocurred)
        self.process.start(str(root_path / "../bin/xi-core.exe").resolve())
        self.process.waitForStarted()

    def on_error_ocurred(self, error):
        if error == QProcess.FailedToStart:
            print("Error ocurred: FailedToStart")
        elif error == QProcess.Crashed:
            print("Error ocurred: Crashed")
        elif error == QProcess.Timedout:
            print("Error ocurred: Timedout")
        elif error == QProcess.WriteError:
            print("Error ocurred: WriteError")
        elif error == QProcess.ReadError:
            print("Error ocurred: ReadError")
        elif error == QProcess.UnknownError:
            print("Error ocurred: UnknownError")

    def read_lines(self):
        while True:
            if self.process.canReadLine():
                line = self.process.readLine().decode("utf8")
            else:
                line = self.process.readAll()

            if line.isEmpty():
                break

            print(line)

    def on_ready_read_standard_output(self):
        print('on_ready_read_standard_output')
        self.read_lines()

    def on_ready_read_standard_error(self):
        print('on_ready_read_standard_error')
        self.read_lines()

    def on_ready_read(self):
        print("on_ready_read")
        self.read_lines()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    x = Foo()
    x.start()
    sys.exit(app.exec_())
