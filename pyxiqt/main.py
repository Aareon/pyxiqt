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
        self.listener.on_data(self, "return_code: {return_code}".encode("utf-8"))


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
            print(repr(data))
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
    new_message = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listener = XiListener()
        self.worker = XiWorker(self.listener)
        self.worker.start()
        self.listener.line_read.connect(self.on_line_read)

    def on_line_read(self, l):
        if l.endswith("fern is set up"):
            print(l)
            return
        if l.endswith("xi-core.log"):
            print(l)
            self.started.emit()
            return
        if not l.strip():
            return

        try:
            self.new_message.emit(json.loads(l))
        except Exception as e:
            self.new_message.emit({"error": str(e)})

    def send(self, data):
        process = self.worker.process
        process.stdin.write(json.dumps(data).encode("utf-8"))
        res = process.communicate()[0]
        if not res.strip():
            return
        self.new_message.emit(json.loads(res.decode("utf-8")))

    # -------- FRONTEND -> BACKEND --------
    # client_started {"config_dir" "some/path"?, "client_extras_dir": "some/other/path"?}
    # close_view {"view_id": "view-id-1"}
    # edit {"method": "insert", "params": {"chars": "A"}, "view_id": "view-id-4"}
        # add_selection_above
        # add_selection_below
        # capitalize
        # clear_recording {"recording_name": string}
        # click [42,31,0,1]
        # collapse_selections
        # copy -> String|Null
        # cut -> String|Null
        # decrease_number
        # delete_backward
        # delete_forward
        # drag [42,32,0]
        # duplicate_line
        # gesture {"line": 42, "col": 31, "ty": "toggle_sel"}
        # point_select # moves the cursor to a point
        # toggle_sel # adds or removes a selection at a point
        # range_select # modifies the selection to include a point (shift+click)
        # line_select # sets the selection to a given line
        # word_select # sets the selection to a given word
        # multi_line_select # adds a line to the selection
        # multi_word_select # adds a word to the selection
        # goto_line {"line": 1}
        # increase_number
        # indent
        # insert {"chars":"A"}
        # insert_newline
        # lowercase
        # move_down
        # move_down_and_modify_selection
        # move_left
        # move_left_and_modify_selection
        # move_right
        # move_right_and_modify_selection
        # move_up
        # move_up_and_modify_selection
        # outdent
        # page_down_and_modify_selection
        # page_up_and_modify_selection
        # paste {"chars": "password"}
        # play_recording {"recording_name": string}
        # resize {width: 420, height: 400}
        # scroll [0,18]
        # scroll_page_down
        # scroll_page_up
        # select_all
        # toggle_recording { "recording_name"?: string}
        # transpose
        # uppercase
        # yank
    # find {"chars": "a", "case_sensitive": false, "regex": false, "whole_words": true}
    # find_all { }
    # find_next {"wrap_around": true, "allow_same": false, "modify_selection": "set"}
    # find_previous {"wrap_around": true, "allow_same": false, "modify_selection": "set"}
    # get_config {"view_id": "view-id-1"} -> Object
    # highlight_find {"visible": true}
    # modify_user_config { "domain": Domain, "changes": Object }
    # multi_find [{"id": 1, "chars": "a", "case_sensitive": false, "regex": false, "whole_words": true}]
    # new_view { "file_path": "path.md"? } -> "view-id-1"
    # plugin {"method": "start", params: {"view_id": "view-id-1", plugin_name: "syntect"}}
    # plugin_rpc {"view_id": "view-id-1", "receiver": "syntect","notification": {"method": "custom_method","params": {"foo": "bar"},}}
    # replace {"chars": "a", "preserve_case": false}
    # replace_all { }
    # replace_next { }
    # save {"view_id": "view-id-4", "file_path": "save.txt"}
    # selection_for_find {"case_sensitive": false}
    # selection_for_replace {"case_sensitive": false}
    # selection_into_lines { }
    # set_language {"view-id":"view-id-1", "language_id":"Rust"}
    # set_theme {"theme_name": "InspiredGitHub"}
    # start {"view_id": "view-id-1", "plugin_name": "syntect"}
    # stop {"view_id": "view-id-1", "plugin_name": "syntect"}

    # -------- BACKEND -> FRONTEND --------
    # add_status_item { "source": "status_example", "key": "my_key", "value": "hello", "alignment": "left" }
    # available_languages {"languages": ["Rust"]}
    # available_plugins {"view_id": "view-id-1", "plugins": [{"name": "syntect", "running": true]}
    # available_themes {"themes": ["InspiredGitHub"]}
    # config_changed {"view_id": "view-id-1", "changes": {} }
    # find_status {"view_id": "view-id-1", "queries": [{"id": 1, "chars": "a", "case_sensitive": false, "is_regex": false, "whole_words": true, "matches": 6, "lines": [1, 3, 3, 6]}]}
    # language_changed {"view_id": "view-id-1", "language_id": "Rust"}
    # plugin_started {"view_id": "view-id-1", "plugin": "syntect"}
    # plugin_stopped {"view_id": "view-id-1", "plugin": "syntect", "code" 101}
    # remove_status_item { "key": "my_key" }
    # replace_status {"view_id": "view-id-1", "status": {"chars": "a", "preserve_case": false}}
    # show_hover { request_id: number, result: string }
    # theme_changed {"name": "InspiredGitHub", "theme": Theme}
    # update_cmds {"view_id": "view-id-1", "plugin", "syntect", "cmds": [Command]}
    # update_status_item { "key": "my_key", "value": "hello"}


class App(QApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xi = XiServer()
        self.xi.started.connect(self.on_started)
        self.xi.new_message.connect(self.on_new_message)

    def on_started(self):
        print("Xi Server - started")
        self.xi.send({
            "method": "client_started",
            "params": {}
        })

    def on_new_message(self, msg):
        method, params = msg["method"], msg["params"]
        if method == "available_themes":
            print(f"Xi Server - {method} - [{','.join(params['themes'])}]")
        elif method == "available_languages":
            print(f"Xi Server - {method} - [{','.join(params['languages'])}]")
        else:
            print("===>", msg)


if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit(app.exec_())
