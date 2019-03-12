from PyQt5.Qt import *
import sys
from pathlib import Path


class Xi(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def start(self):
        root_path = Path(__file__)
        root_path = root_path.parent if root_path.is_file() else root_path
        xi_path = str((root_path / "../bin/xi-core.exe").resolve())

        cmd = self.process = QProcess()
        cmd.setProcessChannelMode(QProcess.MergedChannels)
        cmd.errorOccurred.connect(self.on_error_ocurred)
        cmd.readyRead.connect(self.on_ready_read)
        cmd.started.connect(self.on_started)
        cmd.start(xi_path)

    def on_started(self):
        print('Started process')

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

    def on_ready_read(self):
        while True:
            if self.process.canReadLine():
                line = bytearray(self.process.readLine()).decode("utf8")
            else:
                line = bytearray(self.process.readAll()).decode("utf8")

            if not line.strip():
                break

            print(line, end='')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    x = Xi()
    x.start()
    sys.exit(app.exec_())
