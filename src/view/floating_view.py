# src/view/floating_view.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit,
                             QGraphicsDropShadowEffect, QMenu, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPainter, QBrush
from src.core.theme import AppTheme

class FloatingView(QWidget):
    # Signals
    request_main_window = pyqtSignal()
    request_prev_memo = pyqtSignal()
    request_next_memo = pyqtSignal()
    ontop_toggled = pyqtSignal(bool)

    def __init__(self, settings_model, parent=None):
        super().__init__(parent)
        self.settings = settings_model
        
        # Initial State
        self.is_on_top = self.settings.get("always_on_top", True)
        self.current_content_height = 200
        self.collapsed_height = 6
        self.is_expanded = True
        self._drag_pos = None

        # Setup UI
        self._init_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._init_ui()
        self._init_animations()
        
        # Timer
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.timeout.connect(self.collapse_window)
        self.sync_timer_settings()

        # Initial check
        QTimer.singleShot(100, self.check_enabled_status)

    def _init_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.is_on_top: flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _init_ui(self):
        self.resize(600, self.current_content_height)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet(AppTheme.get_stylesheet("FloatingWindow"))

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 140))
        self.container.setGraphicsEffect(self.shadow)
        self.main_layout.addWidget(self.container)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 12, 16, 12)
        self.container_layout.setSpacing(8)

        self.title_label = QLabel("暂无备忘录")
        self.title_label.setStyleSheet(AppTheme.get_stylesheet("TitleLabel"))
        self.title_label.setWordWrap(True)
        self.title_label.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.container_layout.addWidget(self.title_label)

        self.content_edit = QTextEdit()
        self.content_edit.setReadOnly(True)
        self.content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.content_edit.setStyleSheet(f"""
            QTextEdit {{
                border: none; 
                background: transparent; 
                color: {AppTheme.COLORS['text_primary']};
                line-height: 1.5;
            }}
        """)
        self.container_layout.addWidget(self.content_edit)

    def _init_animations(self):
        self.anim_group = QParallelAnimationGroup(self)
        self.anim_geo = QPropertyAnimation(self, b"geometry")
        self.anim_geo.setDuration(300)
        self.anim_geo.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self.anim_opacity.setDuration(300)

        self.anim_group.addAnimation(self.anim_geo)
        self.anim_group.addAnimation(self.anim_opacity)

    def update_content(self, title, content):
        self.title_label.setText(title)
        self.content_edit.setMarkdown(content)
        self.current_content_height = self._calculate_ideal_height()
        if self.is_expanded:
            self.force_stop_animation()
            self.expand_window()

    def _calculate_ideal_height(self):
        base_width = self.width() - 62
        self.content_edit.document().setTextWidth(base_width)
        doc_height = self.content_edit.document().size().height()
        title_height = self.title_label.sizeHint().height()
        total = int(doc_height + title_height + 60)
        return max(100, min(total, 800))

    def check_enabled_status(self):
        enabled = self.settings.get("show_floating_window", True)
        if not enabled:
            self.hide()
            self.auto_hide_timer.stop()
        else:
            self.restore_position()
            self.show()
            self.expand_window()
            self.auto_hide_timer.start()

    def sync_timer_settings(self):
        seconds = self.settings.get("auto_hide_seconds", 3)
        if seconds < 1: seconds = 1
        self.auto_hide_timer.setInterval(seconds * 1000)

    def force_stop_animation(self):
        self.auto_hide_timer.stop()
        if self.anim_group.state() == QParallelAnimationGroup.State.Running:
            self.anim_group.stop()

    def expand_window(self):
        self.force_stop_animation()
        current_geo = self.geometry()
        target_h = self.current_content_height
        target_geo = QRect(current_geo.x(), 0, current_geo.width(), target_h)

        self.anim_geo.setStartValue(current_geo)
        self.anim_geo.setEndValue(target_geo)
        self.anim_opacity.setStartValue(self.windowOpacity())
        self.anim_opacity.setEndValue(1.0)
        self.anim_group.start()
        self.is_expanded = True

    def collapse_window(self):
        if self.underMouse():
            self.auto_hide_timer.start()
            return
        
        self.force_stop_animation()
        current_geo = self.geometry()
        target_geo = QRect(current_geo.x(), 0, current_geo.width(), self.collapsed_height)

        self.anim_geo.setStartValue(current_geo)
        self.anim_geo.setEndValue(target_geo)
        self.anim_opacity.setStartValue(self.windowOpacity())
        self.anim_opacity.setEndValue(0.5)
        self.anim_group.start()
        self.is_expanded = False
        self.auto_hide_timer.stop()

    def toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            if self.is_expanded:
                self.collapse_window()
            else:
                self.expand_window()
        else:
            self.show()
            self.expand_window()

    def set_always_on_top(self, enabled):
        self.is_on_top = enabled
        pos = self.pos()
        self.hide()
        self._init_window_flags()
        self.move(pos)
        self.show()

    def restore_position(self):
        try:
            x = self.settings.get("win_x")
            if isinstance(x, int):
                self.move(x, 0)
                return
        except:
            pass
        self._center_top_safe()

    def _center_top_safe(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            self.move(x, 0)

    def _save_position(self):
        try:
            self.settings.set("win_x", self.x())
        except:
            pass

    # Events
    def enterEvent(self, event):
        if self.settings.get("show_floating_window", True):
            self.auto_hide_timer.stop()
            self.expand_window()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.sync_timer_settings()
        self.auto_hide_timer.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            self.auto_hide_timer.stop()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos.x(), 0)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            if not self.underMouse():
                self.sync_timer_settings()
                self.auto_hide_timer.start()
            self._save_position()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        if self.height() < 60:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            bar_width = 100
            bar_height = 4
            x = (self.width() - bar_width) // 2
            y = 0
            painter.setBrush(QBrush(QColor(AppTheme.COLORS['accent'])))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_height, 2, 2)
            painter.end()
        else:
            super().paintEvent(event)

    def contextMenuEvent(self, event):
        self.auto_hide_timer.stop()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {AppTheme.COLORS['bg_secondary']}; color: {AppTheme.COLORS['text_primary']}; border: 1px solid {AppTheme.COLORS['border']}; }}
            QMenu::item:selected {{ background-color: {AppTheme.COLORS['accent']}; }}
        """)

        action_main = QAction("显示主窗口", self)
        action_main.triggered.connect(self.request_main_window.emit)
        menu.addAction(action_main)
        menu.addSeparator()

        action_prev = QAction("上一条备忘", self)
        action_prev.triggered.connect(self.request_prev_memo.emit)
        menu.addAction(action_prev)

        action_next = QAction("下一条备忘", self)
        action_next.triggered.connect(self.request_next_memo.emit)
        menu.addAction(action_next)
        menu.addSeparator()

        action_ontop = QAction("保持置顶", self)
        action_ontop.setCheckable(True)
        action_ontop.setChecked(self.is_on_top)
        action_ontop.triggered.connect(lambda checked: self.ontop_toggled.emit(checked))
        menu.addAction(action_ontop)

        action_reset = QAction("重置位置 (居中)", self)
        action_reset.triggered.connect(self._center_top_safe)
        menu.addAction(action_reset)

        action_collapse = QAction("立即收起", self)
        action_collapse.triggered.connect(self.collapse_window)
        menu.addAction(action_collapse)

        menu.exec(event.globalPos())
        if not self.underMouse():
            self.auto_hide_timer.start()
