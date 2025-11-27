# src/utils.py
# -*- coding: utf-8 -*-
import json
import os
import sys
import winreg
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, 'settings.json')
MEMOS_PATH = os.path.join(BASE_DIR, 'memos.json')


class AutoStart:
    def __init__(self, app_name="MemoFlow"):
        self.app_name = app_name
        if getattr(sys, 'frozen', False):
            self.app_path = f'"{sys.executable}"'
        else:
            self.app_path = f'"{sys.executable}" "{os.path.join(BASE_DIR, "main.py")}"'
        self.key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def is_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            return value == self.app_path
        except:
            return False

    def set_state(self, enable=True):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_WRITE)
            if enable:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, self.app_path)
            else:
                try:
                    winreg.DeleteValue(key, self.app_name)
                except:
                    pass
            winreg.CloseKey(key)
            return True
        except:
            return False


class Settings:
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


class DataStore:
    def __init__(self):
        self.file_path = MEMOS_PATH
        self.memos = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.file_path): return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return sorted(data, key=lambda x: x.get('created_at', ''), reverse=True)
        except:
            return []

    def get_memos(self):
        return self.memos

    def add_memo(self, raw_text):
        tags = re.findall(r"#(\S+)", raw_text)
        clean_content = re.sub(r"#\S+", "", raw_text).strip()
        if not clean_content: clean_content = "无标题备忘"

        lines = clean_content.split('\n', 1)
        title = lines[0][:20]

        new_memo = {
            "id": int(datetime.now().timestamp() * 1000),
            "title": title,
            "content": clean_content,
            "tags": tags,
            "created_at": datetime.now().isoformat(),
            "time_str": datetime.now().strftime("%H:%M")
        }
        self.memos.insert(0, new_memo)
        self._save_data()
        return new_memo

    def update_memo(self, memo_id, title, content, tags):
        for memo in self.memos:
            if memo.get("id") == memo_id:
                memo['title'] = title
                memo['content'] = content
                memo['tags'] = tags
                self._save_data()
                return True
        return False

    def delete_memo(self, memo_id):
        initial_len = len(self.memos)
        self.memos = [m for m in self.memos if m.get("id") != memo_id]
        if len(self.memos) < initial_len:
            self._save_data()
            return True
        return False

    def _save_data(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.memos, f, indent=2, ensure_ascii=False)
        except:
            pass
