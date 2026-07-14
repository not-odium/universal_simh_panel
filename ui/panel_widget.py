from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QLabel, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

from .indicators import (LedIndicator, ToggleSwitch, SevenSegmentDisplay,
                          PanelButton, LightRegister, SwitchRegister)
from . import theme_state as _theme


class UniversalPanel(QWidget):
    """Builds a hardware panel from a JSON config dict.

    Supported widget types in config:
        led, toggle, seven_seg, button, light_register, switch_register
    """
    commandRequested = pyqtSignal(str)
    switchChanged = pyqtSignal(str, int)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.widgets: dict = {}
        # Optional authentic "skin": a fixed panel background + label colour
        # (e.g. the burgundy PDP-11/70 console), independent of the app theme.
        self._bg = config.get("background")
        self._label_color = config.get("label_color")
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)
        self.setLayout(outer)

        skinned = bool(self._bg)
        if skinned:
            self.setStyleSheet(
                f"UniversalPanel {{ background-color: {self._bg}; }}")
        title_color = self._label_color or _theme.title_color()
        sep_color = self._label_color or _theme.sep_color()

        title_text = self.config.get("title", "Panel")
        title = QLabel(title_text)
        title.setFont(QFont("Consolas", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {title_color}; padding: 4px; background: transparent;")
        outer.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {sep_color};")
        outer.addWidget(sep)

        for section in self.config.get("sections", []):
            grp = QGroupBox(section.get("title", ""))
            grp.setStyleSheet(self._group_style(skinned, title_color))
            lay = QHBoxLayout()
            lay.setSpacing(8)
            grp.setLayout(lay)

            for wdef in section.get("widgets", []):
                widget = self._create_widget(wdef)
                if widget:
                    wid = wdef.get("id", "")
                    if wid:
                        self.widgets[wid] = widget
                    lay.addWidget(widget)
            lay.addStretch()
            outer.addWidget(grp)

        outer.addStretch()

    def _group_style(self, skinned: bool, title_color: str) -> str:
        if not skinned:
            return _theme.panel_group_style()
        # Borderless, transparent sections so the panel reads as one continuous
        # burgundy surface, like the real console (no boxes around groups).
        return (
            "QGroupBox {"
            " border: none;"
            " margin-top: 12px;"
            " padding: 6px 6px 2px 6px;"
            " background-color: transparent;"
            " font-weight: bold;"
            f" color: {title_color};"
            "}"
            "QGroupBox::title {"
            " subcontrol-origin: margin;"
            " left: 8px; padding: 0 4px;"
            "}"
        )

    def _create_widget(self, wdef: dict) -> QWidget | None:
        wtype = wdef.get("type", "")
        lc = self._label_color

        if wtype == "led":
            return LedIndicator(
                label=wdef.get("label", ""),
                color=wdef.get("color", "green"),
                label_color=lc,
            )
        if wtype == "toggle":
            tw = ToggleSwitch(label=wdef.get("label", ""), label_color=lc)
            wid = wdef.get("id", "")
            tw.toggled.connect(
                lambda st, _id=wid: self.switchChanged.emit(_id, int(st))
            )
            return tw

        if wtype == "seven_seg":
            return SevenSegmentDisplay(
                digits=wdef.get("digits", 4),
                radix=wdef.get("radix", 8),
            )

        if wtype == "button":
            btn = PanelButton(
                label=wdef.get("label", ""),
                color=wdef.get("color", "gray"),
            )
            cmd = wdef.get("command", "")
            if cmd:
                btn.clicked.connect(lambda _c=cmd: self.commandRequested.emit(_c))
            return btn

        if wtype == "light_register":
            return LightRegister(
                bits=wdef.get("bits", 16),
                color=wdef.get("color", "red"),
                color2=wdef.get("color2"),
                label=wdef.get("label", ""),
                group_size=wdef.get("group_size", 3),
                label_color=lc,
            )

        if wtype == "switch_register":
            sr = SwitchRegister(
                bits=wdef.get("bits", 16),
                label=wdef.get("label", ""),
                group_size=wdef.get("group_size", 3),
                color=wdef.get("color", "red"),
                color2=wdef.get("color2"),
                label_color=lc,
            )
            wid = wdef.get("id", "")
            sr.valueChanged.connect(
                lambda v, _id=wid: self.switchChanged.emit(_id, v)
            )
            return sr

        return None

    # --- public helpers for MainWindow state updates -----------------------

    def get_widget(self, widget_id: str):
        return self.widgets.get(widget_id)

    def set_led(self, led_id: str, state: bool):
        w = self.widgets.get(led_id)
        if isinstance(w, LedIndicator):
            w.set_state(state)

    def set_register_value(self, reg_id: str, value: int):
        w = self.widgets.get(reg_id)
        if isinstance(w, (SevenSegmentDisplay, LightRegister)):
            w.set_value(value)

    def get_switch_value(self, sw_id: str) -> int:
        w = self.widgets.get(sw_id)
        if isinstance(w, SwitchRegister):
            return w.get_value()
        return 0

    def reset_all(self):
        for w in self.widgets.values():
            if isinstance(w, LedIndicator):
                w.set_state(False)
            elif isinstance(w, (SevenSegmentDisplay, LightRegister)):
                w.set_value(0)
