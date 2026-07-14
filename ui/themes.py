"""Application colour themes (dark / light), swappable at runtime.

Only the surrounding application chrome (menus, toolbar, terminal, scroll bars)
is themed here; the hardware panel keeps its own dark metal look in either
theme, exactly like a real front panel.
"""

DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
}
QWidget {
    background-color: #2b2b2b;
    color: #d4d4d4;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 10px;
    padding: 10px 6px 6px 6px;
    font-weight: bold;
    color: #999;
    background-color: #333;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QComboBox {
    background-color: #3a3a3a;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 5px 8px;
    color: #ddd;
    min-width: 200px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #aaa;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #3a3a3a;
    color: #ddd;
    selection-background-color: #505050;
    border: 1px solid #555;
}
QMenuBar {
    background-color: #2b2b2b;
    color: #ddd;
    border-bottom: 1px solid #444;
    padding: 2px;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 3px;
}
QMenuBar::item:selected {
    background-color: #444;
}
QMenu {
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
    padding: 4px;
}
QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #505050;
}
QMenu::separator {
    height: 1px;
    background: #555;
    margin: 4px 8px;
}
QStatusBar {
    background-color: #252525;
    color: #aaa;
    border-top: 1px solid #444;
    font-size: 12px;
}
QLabel {
    color: #ccc;
    background-color: transparent;
}
QLineEdit {
    background-color: #3a3a3a;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 6px;
    color: #ddd;
}
QScrollBar:vertical {
    background: #2b2b2b;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QPlainTextEdit {
    border: 1px solid #444;
    border-radius: 4px;
}
QComboBox:hover {
    border: 1px solid #3d7bd6;
}
QComboBox:focus {
    border: 1px solid #4f8ff0;
}
QToolBar#mainToolbar {
    background-color: #232733;
    border-bottom: 1px solid #3a3f4b;
    spacing: 6px;
    padding: 4px 8px;
}
QToolBar#mainToolbar QToolButton {
    background-color: #2f3442;
    color: #dfe4ee;
    border: 1px solid #424857;
    border-radius: 5px;
    padding: 5px 12px;
    font-weight: bold;
}
QToolBar#mainToolbar QToolButton:hover {
    background-color: #3a4150;
    border: 1px solid #4f8ff0;
}
QToolBar#mainToolbar QToolButton:pressed {
    background-color: #273043;
}
QToolBar#mainToolbar QToolButton:disabled {
    color: #5a606e;
    background-color: #262a34;
    border: 1px solid #333845;
}
QScrollArea#panelScroll {
    background-color: #1b1b1b;
    border: none;
}
QScrollBar:horizontal {
    background: #2b2b2b;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #555;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QMenuBar::item:selected {
    background-color: #3d7bd6;
    color: #fff;
}
"""

LIGHT_THEME = """
QMainWindow {
    background-color: #ececec;
}
QWidget {
    background-color: #f4f4f4;
    color: #222;
}
QGroupBox {
    border: 1px solid #bbb;
    border-radius: 5px;
    margin-top: 10px;
    padding: 10px 6px 6px 6px;
    font-weight: bold;
    color: #555;
    background-color: #e6e6e6;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #aaa;
    border-radius: 4px;
    padding: 5px 8px;
    color: #222;
    min-width: 200px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #666;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #222;
    selection-background-color: #cfe0ff;
    border: 1px solid #aaa;
}
QMenuBar {
    background-color: #e6e6e6;
    color: #222;
    border-bottom: 1px solid #ccc;
    padding: 2px;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 3px;
}
QMenuBar::item:selected {
    background-color: #3d7bd6;
    color: #fff;
}
QMenu {
    background-color: #ffffff;
    color: #222;
    border: 1px solid #bbb;
    padding: 4px;
}
QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #cfe0ff;
}
QMenu::separator {
    height: 1px;
    background: #ccc;
    margin: 4px 8px;
}
QStatusBar {
    background-color: #dddddd;
    color: #444;
    border-top: 1px solid #bbb;
    font-size: 12px;
}
QLabel {
    color: #222;
    background-color: transparent;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #aaa;
    border-radius: 4px;
    padding: 4px 6px;
    color: #222;
}
QScrollBar:vertical {
    background: #ececec;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #b7b7b7;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QPlainTextEdit {
    border: 1px solid #bbb;
    border-radius: 4px;
}
QComboBox:hover {
    border: 1px solid #3d7bd6;
}
QComboBox:focus {
    border: 1px solid #4f8ff0;
}
QToolBar#mainToolbar {
    background-color: #dfe6f2;
    border-bottom: 1px solid #c2ccdb;
    spacing: 6px;
    padding: 4px 8px;
}
QToolBar#mainToolbar QToolButton {
    background-color: #eef2f9;
    color: #223;
    border: 1px solid #c2ccdb;
    border-radius: 5px;
    padding: 5px 12px;
    font-weight: bold;
}
QToolBar#mainToolbar QToolButton:hover {
    background-color: #dbe6f7;
    border: 1px solid #4f8ff0;
}
QToolBar#mainToolbar QToolButton:pressed {
    background-color: #cdd9ee;
}
QToolBar#mainToolbar QToolButton:disabled {
    color: #a7adb8;
    background-color: #e6e9ee;
    border: 1px solid #d2d6dd;
}
QScrollArea#panelScroll {
    background-color: #d9d9d9;
    border: none;
}
QScrollBar:horizontal {
    background: #ececec;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #b7b7b7;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
"""
