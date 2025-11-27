# src/settings_ui.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QListWidget, QLineEdit, QPushButton,
                             QSpinBox, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from .utils import AutoStart
from .theme import AppTheme


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.auto_start = AutoStart()

        self.setWindowTitle("设置 - MemoFlow")
        self.resize(400, 650)  # 稍微高一点
        self.setStyleSheet(
            f"background-color: {AppTheme.COLORS['bg_primary']}; color: {AppTheme.COLORS['text_primary']};")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- 1. 常规设置 ---
        group_general = QGroupBox("常规设置")
        group_general.setStyleSheet(self._get_group_style())
        gen_layout = QVBoxLayout(group_general)
        gen_layout.setSpacing(15)

        # 开机自启
        self.cb_autostart = QCheckBox("开机自动启动")
        self.cb_autostart.setStyleSheet(self._get_checkbox_style())
        self.cb_autostart.setChecked(self.auto_start.is_enabled())
        self.cb_autostart.stateChanged.connect(self.on_autostart_changed)
        gen_layout.addWidget(self.cb_autostart)

        # 关闭到托盘
        self.cb_tray = QCheckBox("关闭窗口时最小化到托盘")
        self.cb_tray.setStyleSheet(self._get_checkbox_style())
        self.cb_tray.setChecked(self.settings.get("close_to_tray", True))
        self.cb_tray.stateChanged.connect(lambda s: self.settings.set("close_to_tray", s == 2))
        gen_layout.addWidget(self.cb_tray)

        layout.addWidget(group_general)

        # --- 2. 悬浮窗设置 ---
        group_float = QGroupBox("悬浮窗管理")
        group_float.setStyleSheet(self._get_group_style())
        float_layout = QVBoxLayout(group_float)
        float_layout.setSpacing(15)

        # 启用开关
        self.cb_show_float = QCheckBox("启用桌面悬浮窗")
        self.cb_show_float.setStyleSheet(self._get_checkbox_style())
        self.cb_show_float.setChecked(self.settings.get("show_floating_window", True))
        self.cb_show_float.stateChanged.connect(lambda s: self.settings.set("show_floating_window", s == 2))
        float_layout.addWidget(self.cb_show_float)

        # 保持置顶
        self.cb_ontop = QCheckBox("始终保持在顶部")
        self.cb_ontop.setStyleSheet(self._get_checkbox_style())
        self.cb_ontop.setChecked(self.settings.get("always_on_top", True))
        self.cb_ontop.stateChanged.connect(lambda s: self.settings.set("always_on_top", s == 2))
        float_layout.addWidget(self.cb_ontop)

        # 时间设置行
        time_layout = QHBoxLayout()
        float_lbl = QLabel("鼠标离开后自动淡出 (秒):")
        float_lbl.setStyleSheet(f"color: {AppTheme.COLORS['text_primary']};")

        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(1, 3600)
        self.spin_delay.setValue(self.settings.get("auto_hide_seconds", 3))
        self.spin_delay.setSuffix(" 秒")
        self.spin_delay.setStyleSheet(f"""
            QSpinBox {{
                background-color: {AppTheme.COLORS['bg_secondary']};
                border: 1px solid {AppTheme.COLORS['border']};
                border-radius: 4px;
                padding: 4px;
                color: {AppTheme.COLORS['text_primary']};
            }}
        """)
        self.spin_delay.valueChanged.connect(lambda v: self.settings.set("auto_hide_seconds", v))

        time_layout.addWidget(float_lbl)
        time_layout.addWidget(self.spin_delay)
        float_layout.addLayout(time_layout)

        layout.addWidget(group_float)

        # --- 3. 标签管理 ---
        group_tags = QGroupBox("预设标签管理")
        group_tags.setStyleSheet(self._get_group_style())
        tag_layout = QVBoxLayout(group_tags)

        self.tag_list = QListWidget()
        self.tag_list.setStyleSheet(
            f"QListWidget {{ background-color: {AppTheme.COLORS['bg_secondary']}; border: 1px solid {AppTheme.COLORS['border']}; border-radius: 4px; color: {AppTheme.COLORS['text_primary']}; }}")
        self.refresh_tag_list()
        tag_layout.addWidget(self.tag_list)

        input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("输入新标签...")
        self.tag_input.setStyleSheet(
            f"QLineEdit {{ background-color: {AppTheme.COLORS['bg_secondary']}; border: 1px solid {AppTheme.COLORS['border']}; border-radius: 4px; padding: 5px; color: {AppTheme.COLORS['text_primary']}; }}")
        self.tag_input.returnPressed.connect(self.add_tag)
        input_layout.addWidget(self.tag_input)

        btn_add = QPushButton("添加")
        btn_add.setStyleSheet(self._get_btn_style())
        btn_add.clicked.connect(self.add_tag)
        input_layout.addWidget(btn_add)

        btn_del = QPushButton("删除")
        btn_del.setStyleSheet(self._get_btn_style(danger=True))
        btn_del.clicked.connect(self.del_tag)
        input_layout.addWidget(btn_del)

        tag_layout.addLayout(input_layout)
        layout.addWidget(group_tags)

        layout.addStretch()

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(self._get_btn_style())
        layout.addWidget(btn_close)

    def on_autostart_changed(self, state):
        is_checked = (state == 2)
        if not self.auto_start.set_state(is_checked):
            QMessageBox.warning(self, "权限错误", "无法修改注册表，请以管理员身份运行。")
            self.cb_autostart.blockSignals(True)
            self.cb_autostart.setChecked(not is_checked)
            self.cb_autostart.blockSignals(False)
        else:
            self.settings.set("auto_start", is_checked)

    def refresh_tag_list(self):
        self.tag_list.clear()
        tags = self.settings.get("preset_tags", [])
        self.tag_list.addItems(tags)

    def add_tag(self):
        tag = self.tag_input.text().strip()
        if not tag: return
        tags = self.settings.get("preset_tags", [])
        if tag not in tags:
            tags.append(tag)
            self.settings.set("preset_tags", tags)
            self.refresh_tag_list()
        self.tag_input.clear()

    def del_tag(self):
        row = self.tag_list.currentRow()
        if row >= 0:
            tags = self.settings.get("preset_tags", [])
            del tags[row]
            self.settings.set("preset_tags", tags)
            self.refresh_tag_list()

    def _get_group_style(self):
        return f"""
            QGroupBox {{
                border: 1px solid {AppTheme.COLORS['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                color: {AppTheme.COLORS['text_primary']};
                font-weight: bold;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px; }}
        """

    def _get_checkbox_style(self):
        return f"""
            QCheckBox {{ color: {AppTheme.COLORS['text_primary']}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {AppTheme.COLORS['border']}; border-radius: 4px; background-color: {AppTheme.COLORS['bg_secondary']}; }}
            QCheckBox::indicator:checked {{ background-color: {AppTheme.COLORS['accent']}; border: 1px solid {AppTheme.COLORS['accent']}; }}
        """

    def _get_btn_style(self, danger=False):
        bg = "#e74c3c" if danger else AppTheme.COLORS['accent']
        return f"""
            QPushButton {{ background-color: {bg}; color: white; border-radius: 4px; padding: 6px 12px; border: none; }}
            QPushButton:hover {{ opacity: 0.8; }}
        """
