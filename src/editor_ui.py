# src/editor_ui.py (Beautiful & Stable)
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPlainTextEdit,
                             QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
from .theme import AppTheme


class MemoEditorDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"编辑 - {title}")
        self.resize(500, 400)

        # 窗口样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AppTheme.COLORS['bg_primary']};
                color: {AppTheme.COLORS['text_primary']};
            }}
        """)

        self.final_content = content

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 编辑框样式
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {AppTheme.COLORS['bg_secondary']};
                border: 1px solid {AppTheme.COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                color: {AppTheme.COLORS['text_primary']};
                selection-background-color: {AppTheme.COLORS['accent']};
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {AppTheme.COLORS['accent']};
            }}
        """)
        layout.addWidget(self.text_edit)

        # 按钮组
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("保存修改")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")

        # 按钮样式
        save_style = f"""
            QPushButton {{
                background-color: {AppTheme.COLORS['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #0e8c6d; }}
        """
        cancel_style = f"""
            QPushButton {{
                background-color: {AppTheme.COLORS['bg_secondary']};
                color: {AppTheme.COLORS['text_primary']};
                border: 1px solid {AppTheme.COLORS['border']};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{ background-color: #4a4a4f; }}
        """

        button_box.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(save_style)
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(cancel_style)

        button_box.accepted.connect(self.check_and_save)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def check_and_save(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "内容不能为空")
            return
        self.final_content = text
        self.accept()
