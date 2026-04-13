"""Dark tactical theme for Predator Console."""

THEMES = {
    "Dark Tactical": {
        "colors": {
            "bg_primary": "#1a1a2e",
            "bg_secondary": "#16213e",
            "bg_tertiary": "#0f3460",
            "text_primary": "#e0e0e0",
            "text_secondary": "#a0a0a0",
            "accent": "#e94560",
            "accent_green": "#00ff41",
            "accent_cyan": "#00ffff",
            "accent_yellow": "#ffff00",
            "accent_red": "#ff4444",
            "border": "#333355",
            "input_bg": "#0a0a1a",
            "group_bg": "#1e1e3f",
            "button_primary": "#0f3460",
            "button_primary_text": "#ffffff",
            "button_danger": "#440000",
            "button_safe": "#004400",
            "waterfall_background": "#000000",
        },
        "fonts": {
            "label": "14px",
            "heading": "16px bold",
            "status": "18px bold",
            "monospace": "12px 'Courier New', monospace",
        },
    },
}


def get_theme(name="Dark Tactical"):
    """Return theme dict by name."""
    return THEMES.get(name, THEMES["Dark Tactical"])


def apply_theme_to_app(app, theme_name="Dark Tactical"):
    """Apply global palette to QApplication."""
    from PyQt5 import Qt as q

    theme = get_theme(theme_name)
    c = theme["colors"]

    palette = q.QPalette()
    palette.setColor(q.QPalette.Window, q.QColor(c["bg_primary"]))
    palette.setColor(q.QPalette.WindowText, q.QColor(c["text_primary"]))
    palette.setColor(q.QPalette.Base, q.QColor(c["input_bg"]))
    palette.setColor(q.QPalette.AlternateBase, q.QColor(c["bg_secondary"]))
    palette.setColor(q.QPalette.ToolTipBase, q.QColor(c["bg_tertiary"]))
    palette.setColor(q.QPalette.ToolTipText, q.QColor(c["text_primary"]))
    palette.setColor(q.QPalette.Text, q.QColor(c["text_primary"]))
    palette.setColor(q.QPalette.Button, q.QColor(c["button_primary"]))
    palette.setColor(q.QPalette.ButtonText, q.QColor(c["button_primary_text"]))
    palette.setColor(q.QPalette.BrightText, q.QColor(c["accent_red"]))
    palette.setColor(q.QPalette.Link, q.QColor(c["accent_cyan"]))
    palette.setColor(q.QPalette.Highlight, q.QColor(c["accent"]))
    palette.setColor(q.QPalette.HighlightedText, q.QColor("#ffffff"))

    app.setPalette(palette)


# -- Pre-built stylesheet helpers --


def status_style(color, bg, border=None):
    border = border or color
    return (
        f"font-size: 18px; font-weight: bold; "
        f"background: {bg}; color: {color}; "
        f"border: 2px solid {border}; border-radius: 5px;"
    )


STATUS_OFFLINE = status_style("#555", "#222", "#333")
STATUS_ONLINE = status_style("#0F0", "#040", "#0F0")
STATUS_ACTIVE = status_style("#F00", "#400", "#F00")
STATUS_SILENT = status_style("yellow", "#440", "yellow")


def group_style(t, theme=None):
    """GroupBox title styling."""
    theme = theme or get_theme()
    c = theme["colors"]
    return f"color: {c['text_primary']}; font-weight: bold; font-size: 14px;"


def input_style(theme=None):
    theme = theme or get_theme()
    c = theme["colors"]
    return (
        f"background-color: {c['input_bg']}; color: {c['text_primary']}; "
        f"border: 1px solid {c['border']}; border-radius: 3px; padding: 2px;"
    )


def highlight_input(theme=None):
    theme = theme or get_theme()
    c = theme["colors"]
    return (
        f"background-color: {c['bg_tertiary']}; color: {c['accent_cyan']}; "
        f"font-weight: bold; border: 1px solid {c['border']}; border-radius: 3px;"
    )


def danger_button():
    return "background-color: #440000; color: white; font-weight: bold; border-radius: 3px;"


def safe_button():
    return "background-color: #004400; color: white; font-weight: bold; border-radius: 3px;"


def apply_button_style():
    return "background-color: #004; color: white; font-weight: bold; border-radius: 3px;"


def log_style(theme=None):
    theme = theme or get_theme()
    c = theme["colors"]
    return (
        f"background-color: {c['input_bg']}; color: {c['accent_green']}; "
        f"font-family: 'Courier New', monospace; font-size: 12px;"
    )
