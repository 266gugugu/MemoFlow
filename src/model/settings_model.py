# src/model/settings_model.py
# -*- coding: utf-8 -*-
import json
import os
from src.core.utils import SETTINGS_PATH

class SettingsModel:
    def __init__(self):
        self.file_path = SETTINGS_PATH
        self.config = self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            return {
                "show_floating_window": True,
                "always_on_top": True,
                "close_to_tray": True,
                "auto_start": False,
                "auto_hide_seconds": 3,
                "preset_tags": ["工作", "学习", "生活", "重要"]
            }
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self._save()

    def _save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except:
            pass
