# src/view/main_window.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QSystemTrayIcon, QMenu, QLineEdit, 
                             QPushButton, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QColor, QIcon, QPixmap, QPainter, QBrush

from src.core.theme import AppTheme
from src.view.widgets.memo_item import MemoListItemWidget
from src.view.widgets.tag_button import TagButton

class MainWindow(QMainWindow):
    # Signals
    search_changed = pyqtSignal(str)
    memo_added = pyqtSignal(str)
    memo_clicked = pyqtSignal(int)
    memo_double_clicked = pyqtSignal(int)
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    toggle_floating_requested = pyqtSignal()
    show_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MemoFlow")
        self.resize(400, 600)
        self._init_ui()
        self._init_tray()

    def _init_ui(self):
        self.home_widget = QWidget()
        self.setCentralWidget(self.home_widget)
        
        layout = QVBoxLayout(self.home_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search
        search_container = QWidget()
        search_container.setStyleSheet(f"background-color: {AppTheme.COLORS['bg_primary']}; border-bottom: 1px solid {AppTheme.COLORS['border']};")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 8, 10, 8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索备忘录...")
        self.search_input.setStyleSheet(f"QLineEdit {{ background-color: {AppTheme.COLORS['bg_secondary']}; border: none; border-radius: 15px; padding: 4px 12px; color: {AppTheme.COLORS['text_primary']}; }}")
        self.search_input.textChanged.connect(self.search_changed.emit)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_container)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { border: none; background-color: #1e1e1e; }")
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

        # Input Area
        self._init_input_area(layout)

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
        v_layout.addWidget(self.tag_bar)

        input_row = QWidget()
        input_row.setFixedHeight(50)
        h_layout = QHBoxLayout(input_row)
        h_layout.setContentsMargins(12, 4, 12, 8)
        h_layout.setSpacing(10)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("快速记录... (#标签)")
        self.input_edit.setStyleSheet(f"QLineEdit {{ background-color: #1e1e1e; color: #ECECF1; border: 1px solid #565869; border-radius: 6px; padding: 4px 8px; }} QLineEdit:focus {{ border: 1px solid {AppTheme.COLORS['accent']}; }}")
        self.input_edit.returnPressed.connect(self._on_add_memo)
        h_layout.addWidget(self.input_edit)

        send_btn = QPushButton("发送")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setFixedWidth(60)
        send_btn.setStyleSheet(f"QPushButton {{ background-color: {AppTheme.COLORS['accent']}; color: white; border: none; border-radius: 6px; font-weight: bold; height: 28px; }}")
        send_btn.clicked.connect(self._on_add_memo)
        h_layout.addWidget(send_btn)

        v_layout.addWidget(input_row)
        parent_layout.addWidget(container)

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
        menu.setStyleSheet(f"QMenu {{ background-color: {AppTheme.COLORS['bg_secondary']}; color: {AppTheme.COLORS['text_primary']}; border: 1px solid {AppTheme.COLORS['border']}; }} QMenu::item:selected {{ background-color: {AppTheme.COLORS['accent']}; }}")

        action_show = QAction("显示主窗口", self)
        action_show.triggered.connect(self.show_requested.emit)
        menu.addAction(action_show)

        action_float = QAction("显示/隐藏悬浮窗", self)
        action_float.triggered.connect(self.toggle_floating_requested.emit)
        menu.addAction(action_float)

        action_settings = QAction("设置...", self)
        action_settings.triggered.connect(self.settings_requested.emit)
        menu.addAction(action_settings)

        menu.addSeparator()
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self.quit_requested.emit)
        menu.addAction(action_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def update_memo_list(self, memos):
        self.list_widget.clear()
        for m in memos:
            item = QListWidgetItem(self.list_widget)
            widget = MemoListItemWidget(m.title, m.content, m.tags, m.time_str)
            item.setSizeHint(QSize(0, 80))
            item.setData(Qt.ItemDataRole.UserRole, m.id)
            self.list_widget.setItemWidget(item, widget)

    def update_tag_bar(self, tags):
        while self.tag_bar_layout.count():
            child = self.tag_bar_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        for tag in tags:
            btn = TagButton(tag)
            btn.clicked_tag.connect(self._insert_tag)
            self.tag_bar_layout.addWidget(btn)
        self.tag_bar_layout.addStretch()

    def clear_input(self):
        self.input_edit.clear()

    def scroll_to_top(self):
        self.list_widget.scrollToTop()

    def _on_add_memo(self):
        text = self.input_edit.text().strip()
        if text:
            self.memo_added.emit(text)

    def _insert_tag(self, tag_text):
        current = self.input_edit.text()
        tag_str = f"#{tag_text}"
        if tag_str in current: return
        prefix = " " if current and not current.endswith(" ") else ""
        self.input_edit.setText(f"{current}{prefix}{tag_str} ")
        self.input_edit.setFocus()

    def _on_item_clicked(self, item):
        memo_id = item.data(Qt.ItemDataRole.UserRole)
        self.memo_clicked.emit(memo_id)

    def _on_item_double_clicked(self, item):
        memo_id = item.data(Qt.ItemDataRole.UserRole)
        self.memo_double_clicked.emit(memo_id)

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_requested.emit()

    def closeEvent(self, event):
        # We handle close event in Presenter via Signals, but QMainWindow closeEvent needs to be managed
        # By default, we ignore here and let Presenter decide (hide or quit)
        # But for MVP, View just emits signal. 
        # Actually, it's easier to check logic here or forward to presenter.
        # Let's emit a signal and ignore the event first, Presenter can quit app if needed.
        # BUT standard PyQt way: if we ignore, window stays open. 
        # So we need to know if we should hide or quit.
        # Let's simplify: View asks Presenter "I am closing", Presenter decides what to do.
        # However, closeEvent is synchronous.
        pass # Logic will be injected or handled by Presenter connecting to the window
