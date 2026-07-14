"""Runtime palette for the hardware panel, switched together with the app theme.

Only the panel *surface* (group boxes, titles, painted text labels) follows the
theme.  The physical components themselves — glowing LEDs, seven-segment tubes,
toggle handles, buttons — keep their look in both themes, exactly like real
hardware mounted on a lighter or darker chassis.
"""

_dark = True


def set_dark(dark: bool):
    global _dark
    _dark = dark


def is_dark() -> bool:
    return _dark


def label_color() -> str:
    """Colour for painted labels (LED/register/toggle captions)."""
    return "#b9b9b9" if _dark else "#333333"


def sub_label_color() -> str:
    """Colour for dimmer sub-labels (switch bit numbers)."""
    return "#8c8c8c" if _dark else "#666666"


def title_color() -> str:
    return "#cccccc" if _dark else "#1f1f1f"


def sep_color() -> str:
    return "#555555" if _dark else "#b8b8b8"


def panel_group_style() -> str:
    if _dark:
        bg, border, title = "#333", "#555", "#999"
    else:
        bg, border, title = "#e3e3e3", "#b8b8b8", "#555"
    return f"""
QGroupBox {{
    border: 1px solid {border};
    border-radius: 5px;
    margin-top: 10px;
    padding: 10px 6px 6px 6px;
    background-color: {bg};
    font-weight: bold;
    color: {title};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}
"""
