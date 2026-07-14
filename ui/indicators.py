from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import (QPainter, QColor, QBrush, QPen, QFont,
                          QRadialGradient, QLinearGradient)

from . import theme_state as _theme


LED_COLORS = {
    "green":  ("#00ff44", "#003311"),
    "red":    ("#ff2200", "#330800"),
    "yellow": ("#ffcc00", "#332900"),
    "orange": ("#ff8800", "#331a00"),
    "blue":   ("#4488ff", "#0a1a33"),
    "white":  ("#ffffff", "#333333"),
}

_SEG_MAP = {
    0x0: "abcdef",  0x1: "bc",      0x2: "abdeg",  0x3: "abcdg",
    0x4: "bcfg",    0x5: "acdfg",   0x6: "acdefg", 0x7: "abc",
    0x8: "abcdefg", 0x9: "abcdfg",  0xA: "abcefg", 0xB: "cdefg",
    0xC: "adef",    0xD: "bcdeg",   0xE: "adefg",  0xF: "aefg",
}

# Second colour used for every other group, so triads alternate like the
# painted bands on a real front panel.
_ALT_COLOR = {
    "red": "orange", "orange": "red", "green": "yellow", "yellow": "green",
    "blue": "white", "white": "blue",
}


def _group_gap_after(i, bits, group_size):
    """True if an extra group gap follows element *i* (counted from the left).

    Groups are formed from the least-significant bit, so any remainder lands in
    a shorter leading group on the left — exactly like octal triads on a real
    DEC panel (e.g. 16 bits → 1 + 3 + 3 + 3 + 3 + 3)."""
    lsb = bits - 1 - i
    return lsb != 0 and lsb % group_size == 0


def _group_index(i, bits, group_size):
    """Group number (0 = least-significant group) for alternating colours."""
    return (bits - 1 - i) // group_size


class LedIndicator(QWidget):
    """Single LED indicator with glow effect — mimics real panel lamps."""

    def __init__(self, label="", color="green", label_color=None, parent=None):
        super().__init__(parent)
        self.label = label
        self._label_color = label_color
        self.state = False
        if isinstance(color, str) and color in LED_COLORS:
            self.color_on = QColor(LED_COLORS[color][0])
            self.color_off = QColor(LED_COLORS[color][1])
        else:
            self.color_on = QColor(color) if isinstance(color, str) else QColor("#00ff44")
            self.color_off = self.color_on.darker(500)
        self._led_radius = 7
        nlines = label.count("\n") + 1
        self.setFixedSize(max(40, len(label) * 7 + 10), 44 + 14 * nlines)

    def set_state(self, state: bool):
        if self.state != state:
            self.state = state
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = self.width() // 2
        cy = 14
        r = self._led_radius

        p.setBrush(QBrush(QColor(45, 45, 45)))
        p.setPen(QPen(QColor(70, 70, 70), 1))
        p.drawEllipse(QPointF(cx, cy), r + 3, r + 3)

        if self.state:
            glow = QRadialGradient(cx, cy, r * 3)
            cr, cg, cb = self.color_on.red(), self.color_on.green(), self.color_on.blue()
            glow.setColorAt(0, QColor(cr, cg, cb, 90))
            glow.setColorAt(1, Qt.transparent)
            p.setBrush(QBrush(glow))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx, cy), r * 3, r * 3)

            spec = QRadialGradient(cx - 1.5, cy - 1.5, r * 1.2)
            spec.setColorAt(0, QColor(255, 255, 255, 170))
            spec.setColorAt(0.35, self.color_on)
            spec.setColorAt(1, self.color_on.darker(140))
            p.setBrush(QBrush(spec))
        else:
            p.setBrush(QBrush(self.color_off))

        p.setPen(QPen(QColor(25, 25, 25), 1))
        p.drawEllipse(QPointF(cx, cy), r, r)

        p.setPen(QPen(QColor(self._label_color or _theme.label_color())))
        p.setFont(QFont("Consolas", 7))
        p.drawText(QRectF(0, cy + r + 5, self.width(), self.height() - (cy + r + 5)),
                   Qt.AlignHCenter | Qt.AlignTop, self.label)
        p.end()


class ToggleSwitch(QWidget):
    """Single toggle switch with 3-D metallic look."""
    toggled = pyqtSignal(bool)

    def __init__(self, label="", label_color=None, parent=None):
        super().__init__(parent)
        self.label = label
        self._label_color = label_color
        self.state = False
        nlines = label.count("\n") + 1
        lw = max((len(l) for l in label.split("\n")), default=0)
        self.setFixedSize(max(38, lw * 7 + 8), 74 + 14 * (nlines - 1))
        self.setCursor(Qt.PointingHandCursor)

    def set_state(self, state: bool):
        if self.state != state:
            self.state = state
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.state = not self.state
            self.toggled.emit(self.state)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        cx = w // 2

        base = QRectF(cx - 5, 16, 10, 30)
        bg = QLinearGradient(base.left(), 0, base.right(), 0)
        bg.setColorAt(0, QColor(55, 55, 55))
        bg.setColorAt(0.5, QColor(85, 85, 85))
        bg.setColorAt(1, QColor(55, 55, 55))
        p.setBrush(QBrush(bg))
        p.setPen(QPen(QColor(35, 35, 35), 1))
        p.drawRoundedRect(base, 3, 3)

        hw, hh = 18, 20
        if self.state:
            hy = 4
            hg = QLinearGradient(0, hy, 0, hy + hh)
            hg.setColorAt(0, QColor(210, 65, 65))
            hg.setColorAt(0.5, QColor(180, 45, 45))
            hg.setColorAt(1, QColor(140, 30, 30))
        else:
            hy = 28
            hg = QLinearGradient(0, hy, 0, hy + hh)
            hg.setColorAt(0, QColor(155, 50, 50))
            hg.setColorAt(0.5, QColor(130, 38, 38))
            hg.setColorAt(1, QColor(105, 25, 25))

        p.setBrush(QBrush(hg))
        p.setPen(QPen(QColor(70, 18, 18), 1))
        p.drawRoundedRect(QRectF(cx - hw / 2, hy, hw, hh), 4, 4)

        if self.state:
            p.setPen(QPen(QColor(255, 255, 255, 50), 1))
            p.drawLine(QPointF(cx - hw / 2 + 4, hy + 2),
                       QPointF(cx + hw / 2 - 4, hy + 2))

        p.setPen(QPen(QColor(self._label_color or _theme.label_color())))
        p.setFont(QFont("Consolas", 7))
        p.drawText(QRectF(0, 54, w, self.height() - 54),
                   Qt.AlignHCenter | Qt.AlignTop, self.label)
        p.end()


class SevenSegmentDisplay(QWidget):
    """Multi-digit display with individually-painted segments.

    *radix* selects the base shown on the tubes — 8 (octal, default, as on the
    real DEC/PDP front panels), 16 (hex) or 10 (decimal).
    """

    def __init__(self, digits=4, radix=8, parent=None):
        super().__init__(parent)
        self.digits = digits
        self.radix = radix
        self.value = 0
        self._dw = 22
        self._dh = 38
        self._gap = 5
        self._pad = 6
        total_w = self._pad * 2 + digits * self._dw + (digits - 1) * self._gap
        total_h = self._pad * 2 + self._dh
        self.setFixedSize(total_w, total_h)

    def set_value(self, value: int):
        self.value = value
        self.update()

    @staticmethod
    def _seg_points(seg, x, y, dw, dh):
        l, r = x + 3, x + dw - 3
        t, m, b = y + 2, y + dh // 2, y + dh - 2
        table = {
            "a": (QPointF(l, t), QPointF(r, t)),
            "b": (QPointF(r, t), QPointF(r, m)),
            "c": (QPointF(r, m), QPointF(r, b)),
            "d": (QPointF(l, b), QPointF(r, b)),
            "e": (QPointF(l, m), QPointF(l, b)),
            "f": (QPointF(l, t), QPointF(l, m)),
            "g": (QPointF(l, m), QPointF(r, m)),
        }
        return table.get(seg)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setBrush(QBrush(QColor(12, 12, 12)))
        p.setPen(QPen(QColor(55, 55, 55), 1))
        p.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 4, 4)

        color_on = QColor(255, 28, 8)
        color_off = QColor(38, 7, 4)
        conv = {8: "o", 16: "X", 10: "d"}.get(self.radix, "o")
        text = format(self.value, conv).zfill(self.digits)[-self.digits:]

        for i, ch in enumerate(text):
            dv = int(ch, 16)
            active = _SEG_MAP.get(dv, "")
            ox = self._pad + i * (self._dw + self._gap)
            oy = self._pad
            for s in "abcdefg":
                pts = self._seg_points(s, ox, oy, self._dw, self._dh)
                if pts:
                    c = color_on if s in active else color_off
                    p.setPen(QPen(c, 3, Qt.SolidLine, Qt.RoundCap))
                    p.drawLine(pts[0], pts[1])
        p.end()


class PanelButton(QWidget):
    """Push-button with 3-D gradient and press animation."""
    clicked = pyqtSignal()

    def __init__(self, label="", color="gray", parent=None):
        super().__init__(parent)
        self.label = label
        self._pressed = False
        self._set_colors(color)
        self.setCursor(Qt.PointingHandCursor)

        lines = label.split("\n")
        mw = max((len(l) * 8 + 24) for l in lines) if lines else 60
        h = len(lines) * 16 + 18
        self.setFixedSize(max(60, mw), max(36, h))

    _COLOR_MAP = {
        "red":    (QColor(180, 50, 50),  QColor(140, 35, 35),  QColor(100, 20, 20)),
        "green":  (QColor(50, 160, 50),  QColor(35, 130, 35),  QColor(20, 90, 20)),
        "blue":   (QColor(50, 80, 180),  QColor(35, 60, 140),  QColor(20, 40, 100)),
        "yellow": (QColor(200, 180, 50), QColor(160, 140, 35), QColor(120, 100, 20)),
        "gray":   (QColor(120, 120, 120), QColor(90, 90, 90),  QColor(60, 60, 60)),
        "orange": (QColor(200, 120, 40), QColor(160, 90, 30),  QColor(120, 60, 20)),
    }

    def _set_colors(self, color):
        if isinstance(color, str) and color.startswith("#"):
            base = QColor(color)
            self._c_top, self._c_mid, self._c_bot = (
                base.lighter(125), base, base.darker(140))
            return
        c = self._COLOR_MAP.get(color, self._COLOR_MAP["gray"])
        self._c_top, self._c_mid, self._c_bot = c

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            self.clicked.emit()
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)

        g = QLinearGradient(0, 0, 0, self.height())
        if self._pressed:
            g.setColorAt(0, self._c_bot)
            g.setColorAt(1, self._c_mid)
            border = QColor(30, 30, 30)
        else:
            g.setColorAt(0, self._c_top)
            g.setColorAt(0.5, self._c_mid)
            g.setColorAt(1, self._c_bot)
            border = QColor(65, 65, 65)

        p.setBrush(QBrush(g))
        p.setPen(QPen(border, 1.5))
        p.drawRoundedRect(r, 6, 6)

        p.setPen(QPen(QColor(235, 235, 235)))
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.drawText(r, Qt.AlignCenter, self.label)

        if not self._pressed:
            p.setPen(QPen(QColor(255, 255, 255, 45), 1))
            p.drawLine(QPointF(8, 3), QPointF(self.width() - 8, 3))
        p.end()


class LightRegister(QWidget):
    """Row of small LEDs representing bits of a register value."""

    def __init__(self, bits=16, color="red", label="", group_size=3,
                 color2=None, label_color=None, parent=None):
        super().__init__(parent)
        self.bits = bits
        self.label = label
        self._label_color = label_color
        self._value = 0
        self._group_size = group_size

        color2 = color2 or _ALT_COLOR.get(color, color)
        self._color_on, self._color_off = self._resolve(color)
        self._color_on2, self._color_off2 = self._resolve(color2)

        self._led_d = 9
        self._spacing = 3
        self._grp_extra = 7
        tw = self._total_width()
        self.setFixedSize(tw + 14, 48 if label else 34)

    @staticmethod
    def _resolve(color):
        if color in LED_COLORS:
            return QColor(LED_COLORS[color][0]), QColor(LED_COLORS[color][1])
        return QColor(color), QColor(color).darker(500)

    def _total_width(self):
        w = 0
        for i in range(self.bits):
            w += self._led_d + self._spacing
            if _group_gap_after(i, self.bits, self._group_size):
                w += self._grp_extra
        return w

    def set_value(self, value: int):
        self._value = value
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        x = 7
        y = 18 if self.label else 6

        if self.label:
            p.setPen(QPen(QColor(self._label_color or _theme.label_color())))
            p.setFont(QFont("Consolas", 7))
            p.drawText(QRectF(0, 0, self.width(), 15), Qt.AlignCenter, self.label)

        d = self._led_d
        for i in range(self.bits):
            bit_idx = self.bits - 1 - i
            on = bool(self._value & (1 << bit_idx))
            cx_led = x + d / 2
            cy_led = y + d / 2

            # Alternate the colour of every other group (triad).
            alt = _group_index(i, self.bits, self._group_size) % 2 == 1
            color_on = self._color_on2 if alt else self._color_on
            color_off = self._color_off2 if alt else self._color_off

            if on:
                gl = QRadialGradient(cx_led, cy_led, d)
                cr, cg, cb = color_on.red(), color_on.green(), color_on.blue()
                gl.setColorAt(0, QColor(cr, cg, cb, 70))
                gl.setColorAt(1, Qt.transparent)
                p.setBrush(QBrush(gl))
                p.setPen(Qt.NoPen)
                p.drawEllipse(QRectF(x - 3, y - 3, d + 6, d + 6))

                sp = QRadialGradient(cx_led - 1, cy_led - 1, d / 2)
                sp.setColorAt(0, QColor(255, 255, 255, 150))
                sp.setColorAt(0.4, color_on)
                sp.setColorAt(1, color_on.darker(130))
                p.setBrush(QBrush(sp))
            else:
                p.setBrush(QBrush(color_off))

            p.setPen(QPen(QColor(25, 25, 25), 0.5))
            p.drawEllipse(QRectF(x, y, d, d))

            x += d + self._spacing
            if _group_gap_after(i, self.bits, self._group_size):
                x += self._grp_extra

        p.end()


class SwitchRegister(QWidget):
    """Row of toggle switches representing individual bits."""
    valueChanged = pyqtSignal(int)

    def __init__(self, bits=16, label="", group_size=3,
                 color="red", color2=None, label_color=None, parent=None):
        super().__init__(parent)
        self.bits = bits
        self.label = label
        self._label_color = label_color
        self._value = 0
        self._group_size = group_size
        color2 = color2 or _ALT_COLOR.get(color, "orange")
        self._base = self._sw_color(color)
        self._base2 = self._sw_color(color2)
        self._sw_w = 18
        self._sw_h = 30
        self._spacing = 2
        self._grp_extra = 8
        tw = self._total_width()
        self.setFixedSize(tw + 14, 78 if label else 64)
        self.setCursor(Qt.PointingHandCursor)

    @staticmethod
    def _sw_color(color):
        if color in LED_COLORS:
            return QColor(LED_COLORS[color][0]).darker(140)
        return QColor(color)

    def _total_width(self):
        w = 0
        for i in range(self.bits):
            w += self._sw_w + self._spacing
            if _group_gap_after(i, self.bits, self._group_size):
                w += self._grp_extra
        return w

    def get_value(self):
        return self._value

    def set_value(self, value: int):
        self._value = value
        self.update()

    def _switch_x(self, index):
        x = 7
        for i in range(index):
            x += self._sw_w + self._spacing
            if _group_gap_after(i, self.bits, self._group_size):
                x += self._grp_extra
        return x

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        mx = event.x()
        for i in range(self.bits):
            sx = self._switch_x(i)
            if sx <= mx <= sx + self._sw_w:
                self._value ^= (1 << (self.bits - 1 - i))
                self.valueChanged.emit(self._value)
                self.update()
                return

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        y0 = 18 if self.label else 4

        if self.label:
            p.setPen(QPen(QColor(self._label_color or _theme.label_color())))
            p.setFont(QFont("Consolas", 7))
            p.drawText(QRectF(0, 0, self.width(), 15), Qt.AlignCenter, self.label)

        for i in range(self.bits):
            bit_idx = self.bits - 1 - i
            on = bool(self._value & (1 << bit_idx))
            x = self._switch_x(i)

            # Alternate the handle colour of every other group (triad).
            alt = _group_index(i, self.bits, self._group_size) % 2 == 1
            base = self._base2 if alt else self._base

            base_r = QRectF(x + self._sw_w / 2 - 3, y0 + 4, 6, self._sw_h - 4)
            bg = QLinearGradient(base_r.left(), 0, base_r.right(), 0)
            bg.setColorAt(0, QColor(48, 48, 48))
            bg.setColorAt(0.5, QColor(75, 75, 75))
            bg.setColorAt(1, QColor(48, 48, 48))
            p.setBrush(QBrush(bg))
            p.setPen(QPen(QColor(32, 32, 32), 0.5))
            p.drawRoundedRect(base_r, 2, 2)

            hw, hh = self._sw_w - 4, 13
            hx = x + 2
            if on:
                hy = y0
                hg = QLinearGradient(0, hy, 0, hy + hh)
                hg.setColorAt(0, base.lighter(125))
                hg.setColorAt(1, base.darker(135))
            else:
                hy = y0 + self._sw_h - hh
                hg = QLinearGradient(0, hy, 0, hy + hh)
                hg.setColorAt(0, base.darker(130))
                hg.setColorAt(1, base.darker(175))

            p.setBrush(QBrush(hg))
            p.setPen(QPen(QColor(60, 18, 18), 0.5))
            p.drawRoundedRect(QRectF(hx, hy, hw, hh), 3, 3)

            p.setPen(QPen(QColor(self._label_color or _theme.sub_label_color())))
            p.setFont(QFont("Consolas", 6))
            lr = QRectF(x, y0 + self._sw_h + 3, self._sw_w, 12)
            p.drawText(lr, Qt.AlignCenter, str(bit_idx))

        p.end()
