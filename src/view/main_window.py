# src/view/main_window.py
# -*- coding: utf-8 -*-
"""
MemoFlow v2.0 主窗口

重构要点:
- QListWidget → QListView + MemoListModel
- MemoListItemWidget → MemoDelegate (QPainter 绘制)
- 保持原有信号接口兼容
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListView, QSystemTrayIcon, QMenu, QLineEdit, 
                             QPushButton, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QAction, QColor, QIcon, QPixmap, QPainter, QBrush

from src.core.theme import AppTheme
from src.view.memo_delegate import MemoDelegate
from src.view.widgets.tag_button import TagButton
from src.model.memo_list_model import MemoListModel


class MainWindow(QMainWindow):
    """
    MemoFlow 主窗口 (v2.0)
    
    使用 QListView + MemoListModel 实现高性能虚拟列表
    """
    
    # Signals (保持兼容)
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
        
        # 内部组件
        self._model: MemoListModel = None
        self._delegate = MemoDelegate()
        
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
        search_layout.setContentsMargins(16, 12, 16, 12) # Increased margins

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索备忘录...")
        self.search_input.setStyleSheet(AppTheme.get_stylesheet("SearchInput"))
        self.search_input.textChanged.connect(self.search_changed.emit)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_container)

        # ========================================
        # v2.0: QListView 替代 QListWidget
        # ========================================
        self.list_view = QListView()
        self.list_view.setStyleSheet(AppTheme.get_stylesheet("ListView"))
        self.list_view.setItemDelegate(self._delegate)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_view.setUniformItemSizes(True)  # 性能优化
        self.list_view.setSpacing(4) # Add spacing between items
        
        # 连接点击信号
        self.list_view.clicked.connect(self._on_item_clicked)
        self.list_view.doubleClicked.connect(self._on_item_double_clicked)
        
        layout.addWidget(self.list_view)

        # Input Area
        self._init_input_area(layout)

    def _init_input_area(self, parent_layout):
        container = QWidget()
        container.setStyleSheet(f"background-color: {AppTheme.COLORS['bg_secondary']}; border-top: 1px solid {AppTheme.COLORS['border']};")
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)

        self.tag_bar = QWidget()
        self.tag_bar.setFixedHeight(34) # Slightly taller
        self.tag_bar_layout = QHBoxLayout(self.tag_bar)
        self.tag_bar_layout.setContentsMargins(12, 6, 12, 0)
        self.tag_bar_layout.setSpacing(6)
        v_layout.addWidget(self.tag_bar)

        input_row = QWidget()
        input_row.setFixedHeight(56) # Taller input area
        h_layout = QHBoxLayout(input_row)
        h_layout.setContentsMargins(12, 8, 12, 12)
        h_layout.setSpacing(10)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("快速记录... (#标签)")
        self.input_edit.setStyleSheet(AppTheme.get_stylesheet("MemoInput"))
        self.input_edit.returnPressed.connect(self._on_add_memo)
        h_layout.addWidget(self.input_edit)

        send_btn = QPushButton("发送")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setFixedWidth(64)
        send_btn.setFixedHeight(32)
        send_btn.setStyleSheet(AppTheme.get_stylesheet("PrimaryButton"))
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
        menu.setStyleSheet(
            f"QMenu {{ "
            f"background-color: {AppTheme.COLORS['bg_secondary']}; "
            f"color: {AppTheme.COLORS['text_primary']}; "
            f"border: 1px solid {AppTheme.COLORS['border']}; }} "
            f"QMenu::item:selected {{ background-color: {AppTheme.COLORS['accent']}; }}"
        )

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

    # ========================================
    # v2.0: Model 绑定方法
    # ========================================
    
    def setModel(self, model: MemoListModel) -> None:
        """
        绑定 MemoListModel
        
        由 AppController 调用:
            main_window.setModel(controller.model)
        """
        self._model = model
        self.list_view.setModel(model)
    
    def update_memo_list(self, memos) -> None:
        """
        兼容 v1.0 接口
        
        如果已绑定 Model，则通过 Model 更新数据
        否则忽略（应通过 setModel 绑定）
        """
        if self._model:
            self._model.setMemos(memos)

    def update_tag_bar(self, tags):
        while self.tag_bar_layout.count():
            child = self.tag_bar_layout.takeAt(0)
            if child.widget(): 
                child.widget().deleteLater()
        
        for tag in tags:
            btn = TagButton(tag)
            btn.clicked_tag.connect(self._insert_tag)
            self.tag_bar_layout.addWidget(btn)
        self.tag_bar_layout.addStretch()

    def clear_input(self):
        self.input_edit.clear()

    def scroll_to_top(self):
        if self._model and self._model.rowCount() > 0:
            self.list_view.scrollToTop()

    def _on_add_memo(self):
        text = self.input_edit.text().strip()
        if text:
            self.memo_added.emit(text)

    def _insert_tag(self, tag_text):
        current = self.input_edit.text()
        tag_str = f"#{tag_text}"
        if tag_str in current: 
            return
        prefix = " " if current and not current.endswith(" ") else ""
        self.input_edit.setText(f"{current}{prefix}{tag_str} ")
        self.input_edit.setFocus()

    def _on_item_clicked(self, index: QModelIndex):
        """v2.0: 从 Model 获取 memo_id"""
        if index.isValid():
            memo_id = index.data(MemoListModel.MemoIdRole)
            if memo_id is not None:
                self.memo_clicked.emit(memo_id)

    def _on_item_double_clicked(self, index: QModelIndex):
        """v2.0: 从 Model 获取 memo_id"""
        if index.isValid():
            memo_id = index.data(MemoListModel.MemoIdRole)
            if memo_id is not None:
                self.memo_double_clicked.emit(memo_id)

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, 
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_requested.emit()

    def closeEvent(self, event):
        # 由 Presenter/Controller 处理
        pass
