# main.py
# -*- coding: utf-8 -*-
"""
MemoFlow v2.0 入口文件

架构变更:
- MainPresenter → AppController
- DataStore (JSON) → DatabaseManager (SQLite)
- 保留 FloatingView、SettingsView 等现有组件
"""

import sys
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout
from PyQt6.QtCore import QObject

from src.controller.app_controller import AppController
from src.view.main_window import MainWindow
from src.view.floating_view import FloatingView
from src.view.editor_view import EditorView
from src.view.settings_view import SettingsView
from src.model.settings_model import SettingsModel
from src.core.utils import AutoStart


class MemoFlowApp(QObject):
    """
    MemoFlow v2.0 应用主类
    
    整合 AppController 与现有 View 组件
    """
    
    def __init__(self):
        super().__init__()
        
        # 核心控制器 (v2.0)
        self.controller = AppController()
        
        # 设置模型 (复用 v1.0)
        self.settings_model = SettingsModel()
        self.auto_start = AutoStart()
        
        # Views
        self.main_window = MainWindow()
        self.floating_window = FloatingView(self.settings_model)
        self.editor_dialog = None
        
        # 状态
        self.current_floating_index = 0
        self.current_edit_id = None
        
        # 初始化
        self._sync_autostart()
        self._connect_signals()
        self._load_initial_data()
    
    def _sync_autostart(self):
        """同步开机自启动状态"""
        try:
            config_enabled = self.settings_model.get("auto_start", False)
            registry_enabled = self.auto_start.is_enabled()
            if config_enabled != registry_enabled:
                self.auto_start.set_state(config_enabled)
        except:
            pass
    
    def _connect_signals(self):
        """连接信号"""
        # Main Window ↔ Controller
        self.main_window.setModel(self.controller.model)
        self.main_window.search_changed.connect(self.controller.search)
        self.main_window.memo_added.connect(self._on_memo_added)
        self.main_window.memo_clicked.connect(self._on_memo_clicked)
        self.main_window.memo_double_clicked.connect(self._on_memo_double_clicked)
        self.main_window.settings_requested.connect(self._open_settings)
        self.main_window.quit_requested.connect(self._quit_app)
        self.main_window.toggle_floating_requested.connect(self.floating_window.toggle_visibility)
        self.main_window.show_requested.connect(self._show_main_window)
        
        # Controller 信号
        self.controller.memo_added.connect(self._after_memo_added)
        self.controller.tags_updated.connect(self.main_window.update_tag_bar)
        
        # Floating Window
        self.floating_window.request_main_window.connect(self._show_main_window)
        self.floating_window.request_prev_memo.connect(lambda: self._navigate_memo(-1))
        self.floating_window.request_next_memo.connect(lambda: self._navigate_memo(1))
        self.floating_window.ontop_toggled.connect(self._on_floating_ontop_toggled)
        
        # Patch closeEvent
        self.main_window.closeEvent = self._on_main_window_close
    
    def _load_initial_data(self):
        """加载初始数据"""
        self.controller.load_memos()
        self.controller.load_tags()
        # 加载 preset_tags
        preset_tags = self.settings_model.get("preset_tags", [])
        self.main_window.update_tag_bar(preset_tags)
    
    def start(self):
        """启动应用"""
        self.main_window.show()
    
    # ========================================
    # Main Window 事件处理
    # ========================================
    
    def _on_main_window_close(self, event):
        if self.settings_model.get("close_to_tray", True):
            event.ignore()
            self.main_window.hide()
        else:
            self._quit_app()
    
    def _show_main_window(self):
        self.main_window.show()
        self.main_window.activateWindow()
    
    def _on_memo_added(self, text):
        """处理新增备忘录"""
        self.controller.add_memo(text)
    
    def _after_memo_added(self, memo_id):
        """备忘录添加完成后"""
        self.main_window.clear_input()
        self.main_window.scroll_to_top()
    
    def _on_memo_clicked(self, memo_id):
        """点击备忘录"""
        memo = self.controller.model.getMemoById(memo_id)
        if memo:
            # 更新浮动窗口索引
            row = self.controller.model.getRowById(memo_id)
            if row >= 0:
                self.current_floating_index = row
            
            self.floating_window.update_content(memo.title, memo.content)
            self.floating_window.show()
            self.floating_window.expand_window()
    
    def _on_memo_double_clicked(self, memo_id):
        """双击备忘录 - 打开编辑器"""
        memo = self.controller.model.getMemoById(memo_id)
        if memo:
            self._open_editor(memo)
    
    # ========================================
    # 编辑器
    # ========================================
    
    def _open_editor(self, memo):
        self.current_edit_id = memo.id
        
        self.editor_dialog_window = QDialog(self.main_window)
        self.editor_dialog_window.setWindowTitle(f"编辑 - {memo.title}")
        self.editor_dialog_window.resize(500, 400)
        
        self.editor_view = EditorView(self.editor_dialog_window)
        layout = QVBoxLayout(self.editor_dialog_window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor_view)
        
        preset_tags = self.settings_model.get("preset_tags", [])
        self.editor_view.set_content(memo.title, memo.content, memo.tags, preset_tags)
        
        self.editor_view.save_requested.connect(self._on_editor_save)
        self.editor_view.cancel_requested.connect(self.editor_dialog_window.reject)
        self.editor_view.delete_requested.connect(self._on_editor_delete)
        
        self.editor_dialog_window.exec()
        self.current_edit_id = None
    
    def _on_editor_save(self, title, content, tags):
        if self.current_edit_id:
            # 组合 title 和 content
            full_content = f"{title}\n{content}" if title != content.split('\n')[0] else content
            self.controller.update_memo(self.current_edit_id, full_content, tags)
            self.floating_window.update_content(title, content)
        self.editor_dialog_window.accept()
    
    def _on_editor_delete(self):
        if self.current_edit_id:
            self.controller.delete_memo(self.current_edit_id)
        self.editor_dialog_window.accept()
    
    # ========================================
    # Floating Window
    # ========================================
    
    def _navigate_memo(self, offset):
        model = self.controller.model
        if len(model) == 0:
            return
        
        new_index = (self.current_floating_index + offset) % len(model)
        self.current_floating_index = new_index
        memo = model.getMemo(new_index)
        if memo:
            self.floating_window.update_content(memo.title, memo.content)
    
    def _on_floating_ontop_toggled(self, checked):
        self.settings_model.set("always_on_top", checked)
        self.floating_window.set_always_on_top(checked)
    
    # ========================================
    # Settings
    # ========================================
    
    def _open_settings(self):
        is_autostart = self.auto_start.is_enabled()
        dialog = SettingsView(self.settings_model, is_autostart, self.main_window)
        
        dialog.autostart_toggled.connect(self._on_setting_autostart)
        dialog.closetotray_toggled.connect(lambda c: self.settings_model.set("close_to_tray", c))
        dialog.floating_toggled.connect(self._on_setting_floating_toggled)
        dialog.ontop_toggled.connect(self._on_floating_ontop_toggled)
        dialog.autohide_changed.connect(lambda v: self.settings_model.set("auto_hide_seconds", v))
        dialog.preset_tags_changed.connect(lambda t: self.settings_model.set("preset_tags", t))
        
        if dialog.exec():
            preset_tags = self.settings_model.get("preset_tags", [])
            self.main_window.update_tag_bar(preset_tags)
            self.floating_window.check_enabled_status()
    
    def _on_setting_autostart(self, checked):
        success = self.auto_start.set_state(checked)
        if success:
            self.settings_model.set("auto_start", checked)
    
    def _on_setting_floating_toggled(self, checked):
        self.settings_model.set("show_floating_window", checked)
        self.floating_window.check_enabled_status()
    
    def _quit_app(self):
        self.controller.shutdown()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    memo_app = MemoFlowApp()
    memo_app.start()

    ret = app.exec()
    sys.exit(ret)


if __name__ == "__main__":
    main()
