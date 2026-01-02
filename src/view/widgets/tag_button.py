# src/view/widgets/tag_button.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from src.core.theme import AppTheme

class TagButton(QPushButton):
    """可点击的标签按钮"""
    clicked_tag = pyqtSignal(str) # 发射标签文本

    def __init__(self, text, parent=None):
        super().__init__(f"#{text}", parent)
        self.tag_text = text
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppTheme.COLORS['tag_bg']};
                color: {AppTheme.COLORS['accent']};
                border: 1px solid {AppTheme.COLORS['accent']};
                border-radius: 12px;
                padding: 2px 8px;
                font-size: 11px;
                margin-right: 4px;
            }}
            QPushButton:hover {{
                background-color: {AppTheme.COLORS['accent']};
                color: white;
            }}
        """)
        self.clicked.connect(lambda: self.clicked_tag.emit(self.tag_text))
