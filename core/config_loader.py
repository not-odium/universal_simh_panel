import json
import os
import sys
from typing import Dict, Any


class ConfigLoader:
    """Loads JSON configs relative to the project root (not CWD)."""

    def __init__(self, config_dir: str | None = None):
        if config_dir is None:
            # Support PyInstaller's _MEIPASS for bundled builds
            if getattr(sys, "frozen", False):
                root = sys._MEIPASS
            else:
                root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(root, "config")
        self.config_dir = config_dir

    def load_simh_config(self) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, "simh_config.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"simulators": []}

    def load_panel_config(self, simulator_name: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, "panel_config.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                all_configs = json.load(f)
            return all_configs.get(simulator_name, {"title": simulator_name, "sections": []})
        except Exception:
            return {"title": simulator_name, "sections": []}
