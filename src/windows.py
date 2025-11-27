# src/windows.py
# -*- coding: utf-8 -*-
import re
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QGraphicsDropShadowEffect, QListWidget, QListWidgetItem,
                             QSystemTrayIcon, QMenu, QStyle, QApplication, QLineEdit, QPushButton, QMessageBox,
                             QStackedWidget, QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QAction, QColor, QCursor, QIcon, QPixmap, QPainter, QBrush, QPen

from .theme import AppTheme
from .widgets import MemoListItemWidget, TagButton
from .utils import DataStore, Settings
from .settings_ui import SettingsDialog
from .floating_window import FloatingMemoWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.data_store = DataStore()

        self.setWindowTitle("MemoFlow")
        self.resize(400, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._init_home_page()
        self._init_editor_page()

        self._init_tray()

        # 悬浮窗实例
        self.floating_window = FloatingMemoWindow(self.settings)

        # 连接悬浮窗信号 (上下切换 + 显示主窗)
        self.floating_window.request_main_window.connect(self.show_and_activate)
        self.floating_window.request_prev_memo.connect(lambda: self.navigate_memo(-1))
        self.floating_window.request_next_memo.connect(lambda: self.navigate_memo(1))

        self.current_floating_index = 0
        self.refresh_data()

    # --- 悬浮窗交互逻辑 ---
    def show_and_activate(self):
        self.show()
        self.activateWindow()

    def navigate_memo(self, offset):
        count = self.list_widget.count()
        if count == 0: return
        new_index = (self.current_floating_index + offset) % count
        self.current_floating_index = new_index
        item = self.list_widget.item(new_index)
        self.on_item_clicked(item)

    # ====================== 1. 首页 ======================
    def _init_home_page(self):
        self.home_widget = QWidget()
        layout = QVBoxLayout(self.home_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 搜索框
        search_container = QWidget()
        search_container.setStyleSheet(
            f"background-color: {AppTheme.COLORS['bg_primary']}; border-bottom: 1px solid {AppTheme.COLORS['border']};")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 8, 10, 8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索备忘录...")
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {AppTheme.COLORS['bg_secondary']}; border: none; border-radius: 15px; padding: 4px 12px; color: {AppTheme.COLORS['text_primary']}; }}")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_container)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { border: none; background-color: #1e1e1e; }")
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.switch_to_editor)
        layout.addWidget(self.list_widget)

        self._init_input_area(layout)
        self.stack.addWidget(self.home_widget)

    def _init_input_area(self, parent_layout):
        container = QWidget()
        container.setStyleSheet("background-color: #2d2d30; border-top: 1px solid #3e3e42;")
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)

        self.tag_bar = QWidget()
        self.tag_bar.setFixedHeight(30)
        self.tag_bar_layout = QHBoxLayout(self.tag_bar)
        self.tag_bar_layout.setContentsMargins(12, 4, 12, 0)
        self.tag_bar_layout.setSpacing(4)
        self._refresh_tag_bar()
        v_layout.addWidget(self.tag_bar)

        input_row = QWidget()
        input_row.setFixedHeight(50)
        h_layout = QHBoxLayout(input_row)
        h_layout.setContentsMargins(12, 4, 12, 8)
        h_layout.setSpacing(10)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("快速记录... (#标签)")
        self.input_edit.setStyleSheet(
            f"QLineEdit {{ background-color: #1e1e1e; color: #ECECF1; border: 1px solid #565869; border-radius: 6px; padding: 4px 8px; }} QLineEdit:focus {{ border: 1px solid {AppTheme.COLORS['accent']}; }}")
        self.input_edit.returnPressed.connect(self.add_memo)
        h_layout.addWidget(self.input_edit)

        send_btn = QPushButton("发送")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setFixedWidth(60)
        send_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.COLORS['accent']}; color: white; border: none; border-radius: 6px; font-weight: bold; height: 28px; }}")
        send_btn.clicked.connect(self.add_memo)
        h_layout.addWidget(send_btn)

        v_layout.addWidget(input_row)
        parent_layout.addWidget(container)

    # ====================== 2. 编辑页 ======================
    def _init_editor_page(self):
        self.editor_widget = QWidget()
        self.editor_widget.setStyleSheet(f"background-color: {AppTheme.COLORS['bg_primary']};")
        layout = QVBoxLayout(self.editor_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 顶部
        header = QHBoxLayout()
        title_lbl = QLabel("编辑")
        title_lbl.setStyleSheet(f"color: {AppTheme.COLORS['text_secondary']}; font-size: 14px;")
        header.addWidget(title_lbl)
        header.addStretch()

        btn_delete = QPushButton("删除")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setStyleSheet(
            f"QPushButton {{ color: #e74c3c; background: transparent; border: 1px solid #e74c3c; border-radius: 4px; padding: 4px 12px; }} QPushButton:hover {{ background-color: rgba(231, 76, 60, 0.1); }}")
        btn_delete.clicked.connect(self.delete_current_memo)
        header.addWidget(btn_delete)
        layout.addLayout(header)

        # 标题输入
        self.edit_title_input = QLineEdit()
        self.edit_title_input.setPlaceholderText("标题")
        self.edit_title_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                border-bottom: 1px solid {AppTheme.COLORS['border']};
                color: {AppTheme.COLORS['text_primary']};
                font-size: 18px;
                font-weight: bold;
                padding: 4px 0px;
            }}
            QLineEdit:focus {{ border-bottom: 1px solid {AppTheme.COLORS['accent']}; }}
        """)
        layout.addWidget(self.edit_title_input)

        # 正文输入
        self.editor_text = QTextEdit()
        self.editor_text.setPlaceholderText("Markdown 内容...")
        self.editor_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {AppTheme.COLORS['bg_secondary']};
                border: 1px solid {AppTheme.COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                color: {AppTheme.COLORS['text_primary']};
            }}
        """)
        layout.addWidget(self.editor_text)

        # 标签选择
        tags_label = QLabel("选择标签:")
        tags_label.setStyleSheet(f"color: {AppTheme.COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(tags_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(80)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.tag_select_container = QWidget()
        self.tag_select_layout = QGridLayout(self.tag_select_container)
        self.tag_select_layout.setContentsMargins(0, 0, 0, 0)
        self.tag_select_layout.setSpacing(8)
        self.tag_select_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.tag_select_container)
        layout.addWidget(scroll)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.back_to_home)
        btn_cancel.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.COLORS['bg_secondary']}; color: {AppTheme.COLORS['text_primary']}; border: 1px solid {AppTheme.COLORS['border']}; border-radius: 4px; padding: 8px 20px; }} QPushButton:hover {{ background-color: #4a4a4f; }}")

        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_current_memo)
        btn_save.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.COLORS['accent']}; color: white; border: none; border-radius: 4px; padding: 8px 20px; font-weight: bold; }} QPushButton:hover {{ background-color: #0e8c6d; }}")

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        self.stack.addWidget(self.editor_widget)
        self.current_edit_id = None

    # ====================== 核心逻辑 ======================
    def switch_to_editor(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data: return
        self.current_edit_id = data.get('id')

        # 直接读取纯净数据
        clean_content = data.get('content', '')
        current_title = data.get('title', '')
        existing_tags = data.get('tags', [])

        self.edit_title_input.setText(current_title)
        self.editor_text.setPlainText(clean_content)
        self._populate_tag_selector(existing_tags)

        self.stack.setCurrentIndex(1)

    def _populate_tag_selector(self, existing_tags):
        while self.tag_select_layout.count():
            child = self.tag_select_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        preset_tags = self.settings.get("preset_tags", [])
        for i, tag in enumerate(preset_tags):
            btn = QPushButton(tag)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if tag in existing_tags: btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {AppTheme.COLORS['bg_secondary']};
                    color: {AppTheme.COLORS['text_secondary']};
                    border: 1px solid {AppTheme.COLORS['border']};
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 12px;
                }}
                QPushButton:checked {{
                    background-color: {AppTheme.COLORS['tag_bg']};
                    color: {AppTheme.COLORS['accent']};
                    border: 1px solid {AppTheme.COLORS['accent']};
                }}
            """)
            self.tag_select_layout.addWidget(btn, i // 4, i % 4)

    def save_current_memo(self):
        if not self.current_edit_id: return

        new_title = self.edit_title_input.text().strip()
        if not new_title: new_title = "无标题"
        new_content = self.editor_text.toPlainText().strip()

        selected_tags = []
        for i in range(self.tag_select_layout.count()):
            widget = self.tag_select_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton) and widget.isChecked():
                selected_tags.append(widget.text())

        if self.data_store.update_memo(self.current_edit_id, new_title, new_content, selected_tags):
            self.refresh_data()
            self.floating_window.update_content(new_title, new_content)

        self.back_to_home()

    def on_search_text_changed(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data: continue
            content_to_search = (data.get('title', '') + data.get('content', '')).lower()
            item.setHidden(text.lower() not in content_to_search)

    def back_to_home(self):
        self.editor_text.clear()
        self.edit_title_input.clear()
        self.current_edit_id = None
        self.stack.setCurrentIndex(0)

    def delete_current_memo(self):
        if not self.current_edit_id: return
        self.data_store.delete_memo(self.current_edit_id)
        self.refresh_data()
        self.back_to_home()

    def on_item_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.current_floating_index = self.list_widget.row(item)
            self.floating_window.update_content(data["title"], data["content"])
            self.floating_window.show()
            self.floating_window.expand_window()

    def _refresh_tag_bar(self):
        while self.tag_bar_layout.count():
            child = self.tag_bar_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        preset_tags = self.settings.get("preset_tags", [])
        for tag in preset_tags:
            btn = TagButton(tag)
            btn.clicked_tag.connect(self.insert_tag)
            self.tag_bar_layout.addWidget(btn)
        self.tag_bar_layout.addStretch()

    def insert_tag(self, tag_text):
        current = self.input_edit.text()
        tag_str = f"#{tag_text}"
        if tag_str in current: return
        prefix = " " if current and not current.endswith(" ") else ""
        self.input_edit.setText(f"{current}{prefix}{tag_str} ")
        self.input_edit.setFocus()

    def add_memo(self):
        text = self.input_edit.text().strip()
        if not text: return
        self.data_store.add_memo(text)
        self.refresh_data()
        self.input_edit.clear()
        self.list_widget.scrollToTop()

    def refresh_data(self):
        self.list_widget.clear()
        self._refresh_tag_bar()
        memos = self.data_store.get_memos()
        for m in memos: self._add_memo_item(m)
        search_text = self.search_input.text()
        if search_text: self.on_search_text_changed(search_text)

    def _add_memo_item(self, memo):
        item = QListWidgetItem(self.list_widget)
        widget = MemoListItemWidget(memo.get('title', ''), memo.get('content', ''), memo.get('tags', []),
                                    memo.get('time_str', ''))
        item.setSizeHint(QSize(0, 80))
        item.setData(Qt.ItemDataRole.UserRole, memo)
        self.list_widget.setItemWidget(item, widget)

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#10A37F")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        self.tray.setIcon(QIcon(pixmap))
        self.tray.setToolTip("MemoFlow")

        menu = QMenu()
        menu.setStyleSheet(
            f"QMenu {{ background-color: {AppTheme.COLORS['bg_secondary']}; color: {AppTheme.COLORS['text_primary']}; border: 1px solid {AppTheme.COLORS['border']}; }} QMenu::item:selected {{ background-color: {AppTheme.COLORS['accent']}; }}")

        action_show = QAction("显示主窗口", self)
        action_show.triggered.connect(self.show)
        menu.addAction(action_show)

        action_float = QAction("显示/隐藏悬浮窗", self)
        action_float.triggered.connect(self.toggle_floating_window)
        menu.addAction(action_float)

        action_settings = QAction("设置...", self)
        action_settings.triggered.connect(self.open_settings)
        menu.addAction(action_settings)

        menu.addSeparator()
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self.quit_app)
        menu.addAction(action_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show()
            self.activateWindow()

    def toggle_floating_window(self):
        self.floating_window.toggle_visibility()

    def open_settings(self):
        try:
            dialog = SettingsDialog(self.settings, self)
            if dialog.exec():
                self._refresh_tag_bar()
                # 刷新悬浮窗状态（以防开关变动）
                self.floating_window.check_enabled_status()
        except:
            pass

    def _init_hotkey(self):
        pass

    def on_hotkey(self):
        self.floating_window.toggle_visibility()

    def quit_app(self):
        QApplication.quit()

    def closeEvent(self, e):
        if self.settings.get("close_to_tray", True):
            e.ignore()
            self.hide()
        else:
            self.quit_app()
