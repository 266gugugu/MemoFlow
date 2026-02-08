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
from PyQt6.QtCore import QObject, QTimer

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
        self.current_floating_memo_id = None  # 使用 ID 而非索引追踪
        self.current_edit_id = None
        
        # 防抖定时器（避免双击时触发两次单击）
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self._process_single_click)
        self.pending_click_id = None
        
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
        """点击备忘录 - 使用防抖避免双击冲突"""
        self.pending_click_id = memo_id
        self.click_timer.start(200)  # 200ms 延迟，双击会取消
    
    def _process_single_click(self):
        """处理实际的单击事件"""
        if self.pending_click_id is None:
            return
        
        memo_id = self.pending_click_id
        self.pending_click_id = None
        
        memo = self.controller.model.getMemoById(memo_id)
        if memo:
            # 更新当前 ID
            self.current_floating_memo_id = memo_id
            
            self.floating_window.update_content(memo.title, memo.content)
            self.floating_window.show()
            self.floating_window.expand_window()
    
    def _on_memo_double_clicked(self, memo_id):
        """双击备忘录 - 取消单击并打开编辑器"""
        self.click_timer.stop()  # 取消待处理的单击
        self.pending_click_id = None
        
        memo = self.controller.model.getMemoById(memo_id)
        if memo:
            self._open_editor(memo)
    
    # ========================================
    # 编辑器
    # ========================================
    
    def _open_editor(self, memo):
        self.current_edit_id = memo.id
        
        # 创建编辑器对话框（每次都是新实例，exec() 阻塞结束后会自动清理）
        self.editor_dialog_window = QDialog(self.main_window)
        self.editor_dialog_window.setWindowTitle(f"编辑 - {memo.title}")
        self.editor_dialog_window.resize(500, 400)
        
        self.editor_view = EditorView(self.editor_dialog_window)
        layout = QVBoxLayout(self.editor_dialog_window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor_view)
        
        # Split content into title (first line) and body (rest)
        title = memo.title
        body = memo.content.partition('\n')[2]
        
        preset_tags = self.settings_model.get("preset_tags", [])
        self.editor_view.set_content(title, body, memo.tags, preset_tags)
        
        # 连接信号（对话框关闭时自动断开，不会泄漏）
        self.editor_view.save_requested.connect(self._on_editor_save)
        self.editor_view.cancel_requested.connect(self.editor_dialog_window.reject)
        self.editor_view.delete_requested.connect(self._on_editor_delete)
        
        self.editor_dialog_window.exec()
        self.current_edit_id = None
    
    def _on_editor_save(self, title, content, tags):
        if self.current_edit_id:
            # Always combine title and content with a newline
            full_content = f"{title}\n{content}"
            self.controller.update_memo(self.current_edit_id, full_content, tags)
            
            # 同步到悬浮窗（如果是当前显示的备忘录）
            if self.current_floating_memo_id == self.current_edit_id:
                self.floating_window.update_content(title, content)
        self.editor_dialog_window.accept()
    
    def _on_editor_delete(self):
        if self.current_edit_id:
            deleted_id = self.current_edit_id
            self.controller.delete_memo(deleted_id)
            
            # 如果删除的是当前悬浮窗显示的备忘录
            if deleted_id == self.current_floating_memo_id:
                self.current_floating_memo_id = None
                # 尝试显示下一条
                if len(self.controller.model) > 0:
                    memo = self.controller.model.getMemo(0)
                    if memo:
                        self.current_floating_memo_id = memo.id
                        self.floating_window.update_content(memo.title, memo.content)
                else:
                    self.floating_window.hide()
        self.editor_dialog_window.accept()
    
    # ========================================
    # Floating Window
    # ========================================
    
    def _navigate_memo(self, offset):
        model = self.controller.model
        if len(model) == 0:
            self.floating_window.hide()
            return
        
        # 如果没有当前 ID，从第一条开始
        if not self.current_floating_memo_id:
            memo = model.getMemo(0)
            if memo:
                self.current_floating_memo_id = memo.id
                self.floating_window.update_content(memo.title, memo.content)
            return
        
        # 找到当前备忘录的行号
        current_row = model.getRowById(self.current_floating_memo_id)
        if current_row < 0:
            # 当前备忘录不在列表中（被删除或过滤），从第一条开始
            memo = model.getMemo(0)
            if memo:
                self.current_floating_memo_id = memo.id
                self.floating_window.update_content(memo.title, memo.content)
            return
        
        # 计算新行号
        new_row = (current_row + offset) % len(model)
        memo = model.getMemo(new_row)
        if memo:
            self.current_floating_memo_id = memo.id
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
        dialog.autohide_changed.connect(lambda v: (
            self.settings_model.set("auto_hide_seconds", v),
            self.floating_window.sync_timer_settings()  # 立即同步
        ))
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
