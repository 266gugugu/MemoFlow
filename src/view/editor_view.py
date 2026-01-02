# src/view/editor_view.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QLineEdit, QPushButton, QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from src.core.theme import AppTheme

class EditorView(QWidget):
    # Signals to Presenter
    save_requested = pyqtSignal(str, str, list)  # title, content, tags
    cancel_requested = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AppTheme.COLORS['bg_primary']};")
        self._init_ui()
        self.current_tags = []

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QHBoxLayout()
        title_lbl = QLabel("编辑")
        title_lbl.setStyleSheet(f"color: {AppTheme.COLORS['text_secondary']}; font-size: 14px;")
        header.addWidget(title_lbl)
        header.addStretch()

        btn_delete = QPushButton("删除")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setStyleSheet(f"""
            QPushButton {{ color: #e74c3c; background: transparent; border: 1px solid #e74c3c; border-radius: 4px; padding: 4px 12px; }} 
            QPushButton:hover {{ background-color: rgba(231, 76, 60, 0.1); }}
        """)
        btn_delete.clicked.connect(self.delete_requested.emit)
        header.addWidget(btn_delete)
        layout.addLayout(header)

        # Title Input
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

        # Content Input
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

        # Tags Selection
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

        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.cancel_requested.emit)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{ background-color: {AppTheme.COLORS['bg_secondary']}; color: {AppTheme.COLORS['text_primary']}; border: 1px solid {AppTheme.COLORS['border']}; border-radius: 4px; padding: 8px 20px; }} 
            QPushButton:hover {{ background-color: #4a4a4f; }}
        """)

        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self._on_save_clicked)
        btn_save.setStyleSheet(f"""
            QPushButton {{ background-color: {AppTheme.COLORS['accent']}; color: white; border: none; border-radius: 4px; padding: 8px 20px; font-weight: bold; }} 
            QPushButton:hover {{ background-color: #0e8c6d; }}
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def set_content(self, title, content, tags, preset_tags):
        self.edit_title_input.setText(title)
        self.editor_text.setPlainText(content)
        self.current_tags = tags
        self._populate_tag_selector(preset_tags, tags)

    def _populate_tag_selector(self, preset_tags, existing_tags):
        # Clear existing
        while self.tag_select_layout.count():
            child = self.tag_select_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

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

    def _on_save_clicked(self):
        new_title = self.edit_title_input.text().strip()
        if not new_title: new_title = "无标题"
        new_content = self.editor_text.toPlainText().strip()
        
        selected_tags = []
        for i in range(self.tag_select_layout.count()):
            widget = self.tag_select_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton) and widget.isChecked():
                selected_tags.append(widget.text())
        
        self.save_requested.emit(new_title, new_content, selected_tags)
