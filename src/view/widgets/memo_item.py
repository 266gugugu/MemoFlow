# src/view/widgets/memo_item.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from src.core.theme import AppTheme

class MemoListItemWidget(QWidget):
    def __init__(self, title, preview, tags, time_str, parent=None):
        super().__init__(parent)
        self.title_text = title or "无标题"
        self.preview_text = preview or "无内容"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 头部
        header = QHBoxLayout()
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet(AppTheme.get_stylesheet("ListTitle"))
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet(AppTheme.get_stylesheet("ListTime"))
        header.addWidget(self.title_label, 1)
        header.addWidget(self.time_label)
        layout.addLayout(header)

        # 预览
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet(AppTheme.get_stylesheet("ListPreview"))
        self.preview_label.setFixedHeight(36)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.preview_label)

        # Tags
        if tags:
            t_layout = QHBoxLayout()
            for tag in tags:
                lbl = QLabel(f"#{tag}")
                lbl.setStyleSheet(AppTheme.get_stylesheet("Tag"))
                t_layout.addWidget(lbl)
            t_layout.addStretch()
            layout.addLayout(t_layout)

        self._elide_text()

    def resizeEvent(self, event):
        self._elide_text()
        super().resizeEvent(event)

    def _elide_text(self):
        fm = QFontMetrics(self.title_label.font())
        self.title_label.setText(fm.elidedText(self.title_text, Qt.TextElideMode.ElideRight, self.title_label.width()))

        fm2 = QFontMetrics(self.preview_label.font())
        self.preview_label.setText(
            fm2.elidedText(self.preview_text, Qt.TextElideMode.ElideRight, self.preview_label.width() * 2))
        self.preview_label.setWordWrap(True)
