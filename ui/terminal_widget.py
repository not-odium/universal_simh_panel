from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QTextCursor


class TerminalWidget(QPlainTextEdit):
    """Green-on-black terminal with command history.

    Thread-safe output: call ``schedule_output(text)`` instead of
    ``append_output`` when writing from a non-GUI thread. The signal
    ``_output_signal`` will marshal the text onto the main thread.
    """
    commandEntered = pyqtSignal(str)
    _output_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_line = ""
        self._prompt = "sim> "
        self._history: list[str] = []
        self._history_idx = -1
        self._output_buffer = ""

        self._init_style()
        self._show_prompt()
        self._output_signal.connect(self._on_output)

    def _init_style(self):
        pal = self.palette()
        pal.setColor(QPalette.Base, QColor(5, 5, 5))
        pal.setColor(QPalette.Text, QColor(0, 230, 0))
        self.setPalette(pal)
        f = QFont("Courier New", 10)
        f.setStyleHint(QFont.Monospace)
        self.setFont(f)
        self.setReadOnly(False)
        self.setUndoRedoEnabled(False)

    def _show_prompt(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(self._prompt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _move_to_end(self):
        c = self.textCursor()
        c.movePosition(QTextCursor.End)
        self.setTextCursor(c)
        self.ensureCursorVisible()

    # --- keyboard ---------------------------------------------------------

    def keyPressEvent(self, event):
        key = event.key()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            cmd = self._current_line.strip()
            if cmd:
                self._history.append(cmd)
                self._history_idx = -1
                self.commandEntered.emit(cmd)
            self._move_to_end()
            cursor = self.textCursor()
            cursor.insertText("\n")
            self.setTextCursor(cursor)
            self._current_line = ""
            self._show_prompt()
            return

        if key == Qt.Key_Backspace:
            if self._current_line:
                self._current_line = self._current_line[:-1]
                self._refresh_line()
            return

        if key == Qt.Key_Up:
            if self._history:
                if self._history_idx == -1:
                    self._history_idx = len(self._history) - 1
                elif self._history_idx > 0:
                    self._history_idx -= 1
                self._current_line = self._history[self._history_idx]
                self._refresh_line()
            return

        if key == Qt.Key_Down:
            if self._history_idx != -1:
                if self._history_idx < len(self._history) - 1:
                    self._history_idx += 1
                    self._current_line = self._history[self._history_idx]
                else:
                    self._history_idx = -1
                    self._current_line = ""
                self._refresh_line()
            return

        if key == Qt.Key_Home:
            return

        text = event.text()
        if text and text.isprintable():
            self._current_line += text
            self._refresh_line()

    def _refresh_line(self):
        self._move_to_end()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        selected = cursor.selectedText()
        if selected.startswith(self._prompt):
            cursor.removeSelectedText()
            cursor.insertText(self._prompt + self._current_line)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    # --- output (thread-safe) ---------------------------------------------

    def schedule_output(self, text: str):
        """Call from any thread to append emulator output."""
        self._output_signal.emit(text)

    def _on_output(self, text: str):
        self._output_buffer += text
        if "\n" not in self._output_buffer:
            return

        lines = self._output_buffer.split("\n")
        self._output_buffer = lines[-1]

        self._move_to_end()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        block = cursor.selectedText()
        if block.startswith(self._prompt):
            cursor.removeSelectedText()
        else:
            cursor.movePosition(QTextCursor.End)

        for line in lines[:-1]:
            stripped = line.rstrip()
            if stripped:
                cursor.insertText(stripped + "\n")

        self.setTextCursor(cursor)
        self._current_line = ""
        self._show_prompt()

    def flush_output(self):
        if self._output_buffer.strip():
            self._on_output(self._output_buffer + "\n")
            self._output_buffer = ""

    def clear_terminal(self):
        """Wipe the terminal and restore a fresh prompt."""
        self.clear()
        self._current_line = ""
        self._output_buffer = ""
        self._show_prompt()
