# src/presenter/main_presenter.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import QObject
from src.core.utils import AutoStart

from src.view.main_window import MainWindow
from src.view.floating_view import FloatingView
from src.view.editor_view import EditorView
from src.view.settings_view import SettingsView

from src.model.data_store import DataStore
from src.model.settings_model import SettingsModel

class MainPresenter(QObject):
    def __init__(self):
        super().__init__()
        # Models
        self.settings_model = SettingsModel()
        self.data_store = DataStore()
        self.auto_start = AutoStart()

        # Views
        self.main_window = MainWindow()
        self.floating_window = FloatingView(self.settings_model)
        self.editor_dialog = None # Created on demand or reused

        # State
        self.current_floating_index = 0
        self.current_edit_id = None

        # Sync AutoStart
        self._sync_autostart()

        # Connections
        self._connect_main_window()
        self._connect_floating_window()

        # Initial Data Load
        self.refresh_data()

    def start(self):
        self.main_window.show()
        # Floating window visibility is handled by its own internal check_enabled_status

    def _sync_autostart(self):
        try:
            config_enabled = self.settings_model.get("auto_start", False)
            registry_enabled = self.auto_start.is_enabled()
            if config_enabled != registry_enabled:
                self.auto_start.set_state(config_enabled)
        except:
            pass

    # --- Main Window Logic ---
    def _connect_main_window(self):
        view = self.main_window
        view.search_changed.connect(self.on_search_changed)
        view.memo_added.connect(self.on_memo_added)
        view.memo_clicked.connect(self.on_memo_clicked)
        view.memo_double_clicked.connect(self.on_memo_double_clicked)
        view.settings_requested.connect(self.open_settings)
        view.quit_requested.connect(self.quit_app)
        view.toggle_floating_requested.connect(self.floating_window.toggle_visibility)
        view.show_requested.connect(self.show_main_window)
        
        # Patch closeEvent
        view.closeEvent = self.on_main_window_close

    def on_main_window_close(self, event):
        if self.settings_model.get("close_to_tray", True):
            event.ignore()
            self.main_window.hide()
        else:
            self.quit_app()

    def show_main_window(self):
        self.main_window.show()
        self.main_window.activateWindow()

    def on_search_changed(self, text):
        memos = self.data_store.get_memos()
        if not text:
            self.main_window.update_memo_list(memos)
            return
        
        filtered = []
        for m in memos:
            if text.lower() in (m.title + m.content).lower():
                filtered.append(m)
        self.main_window.update_memo_list(filtered)

    def on_memo_added(self, text):
        self.data_store.add_memo(text)
        self.refresh_data()
        self.main_window.clear_input()
        self.main_window.scroll_to_top()

    def on_memo_clicked(self, memo_id):
        memo = self.data_store.get_memo_by_id(memo_id)
        if memo:
            # Sync floating window index
            memos = self.data_store.get_memos()
            try:
                self.current_floating_index = memos.index(memo)
            except ValueError:
                self.current_floating_index = 0
            
            self.floating_window.update_content(memo.title, memo.content)
            self.floating_window.show()
            self.floating_window.expand_window()

    def on_memo_double_clicked(self, memo_id):
        memo = self.data_store.get_memo_by_id(memo_id)
        if memo:
            self.open_editor(memo)

    def refresh_data(self):
        memos = self.data_store.get_memos()
        self.main_window.update_memo_list(memos)
        self.main_window.update_tag_bar(self.settings_model.get("preset_tags", []))

    # --- Editor Logic ---
    def open_editor(self, memo):
        self.current_edit_id = memo.id
        
        # Create dialog wrapper
        self.editor_dialog_window = QDialog(self.main_window)
        self.editor_dialog_window.setWindowTitle(f"编辑 - {memo.title}")
        self.editor_dialog_window.resize(500, 400)
        
        # Embed EditorView
        self.editor_view = EditorView(self.editor_dialog_window)
        layout = QVBoxLayout(self.editor_dialog_window)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.editor_view)
        
        # Setup Data
        preset_tags = self.settings_model.get("preset_tags", [])
        self.editor_view.set_content(memo.title, memo.content, memo.tags, preset_tags)
        
        # Connect Signals
        self.editor_view.save_requested.connect(self.on_editor_save)
        self.editor_view.cancel_requested.connect(self.editor_dialog_window.reject)
        self.editor_view.delete_requested.connect(self.on_editor_delete)
        
        self.editor_dialog_window.exec()
        self.current_edit_id = None

    def on_editor_save(self, title, content, tags):
        if self.current_edit_id:
            if self.data_store.update_memo(self.current_edit_id, title, content, tags):
                self.refresh_data()
                self.floating_window.update_content(title, content)
        self.editor_dialog_window.accept()

    def on_editor_delete(self):
        if self.current_edit_id:
            self.data_store.delete_memo(self.current_edit_id)
            self.refresh_data()
        self.editor_dialog_window.accept()

    # --- Floating Window Logic ---
    def _connect_floating_window(self):
        view = self.floating_window
        view.request_main_window.connect(self.show_main_window)
        view.request_prev_memo.connect(lambda: self.navigate_memo(-1))
        view.request_next_memo.connect(lambda: self.navigate_memo(1))
        view.ontop_toggled.connect(self.on_floating_ontop_toggled)

    def navigate_memo(self, offset):
        memos = self.data_store.get_memos()
        if not memos: return
        
        new_index = (self.current_floating_index + offset) % len(memos)
        self.current_floating_index = new_index
        memo = memos[new_index]
        self.floating_window.update_content(memo.title, memo.content)

    def on_floating_ontop_toggled(self, checked):
        self.settings_model.set("always_on_top", checked)
        self.floating_window.set_always_on_top(checked)

    # --- Settings Logic ---
    def open_settings(self):
        is_autostart = self.auto_start.is_enabled()
        dialog = SettingsView(self.settings_model, is_autostart, self.main_window)
        
        dialog.autostart_toggled.connect(self.on_setting_autostart)
        dialog.closetotray_toggled.connect(lambda c: self.settings_model.set("close_to_tray", c))
        dialog.floating_toggled.connect(self.on_setting_floating_toggled)
        dialog.ontop_toggled.connect(lambda c: self.on_floating_ontop_toggled(c))
        dialog.autohide_changed.connect(lambda v: self.settings_model.set("auto_hide_seconds", v))
        dialog.preset_tags_changed.connect(lambda t: self.settings_model.set("preset_tags", t))
        
        if dialog.exec():
            self.main_window.update_tag_bar(self.settings_model.get("preset_tags", []))
            self.floating_window.check_enabled_status()

    def on_setting_autostart(self, checked):
        success = self.auto_start.set_state(checked)
        if success:
            self.settings_model.set("auto_start", checked)
        else:
            # Revert UI if failed (would need reference to dialog, simplifying for MVP)
            pass 

    def on_setting_floating_toggled(self, checked):
        self.settings_model.set("show_floating_window", checked)
        self.floating_window.check_enabled_status()

    def quit_app(self):
        QApplication.quit()
