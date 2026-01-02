# src/core/utils.py
# -*- coding: utf-8 -*-
import os
import sys
import winreg

# 定义全局路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
