# src/view/memo_delegate.py
# -*- coding: utf-8 -*-
"""
备忘录列表项委托 (高性能渲染)

核心设计:
- 使用 QPainter 手动绘制，避免创建数千个 QWidget
- 内存占用近乎为零，滚动极其丝滑
- 支持深色主题
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QApplication
from PyQt6.QtCore import QSize, QRect, Qt, QModelIndex
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontMetrics

from src.model.memo_list_model import MemoListModel


class MemoDelegate(QStyledItemDelegate):
    """
    高性能备忘录项绘制委托
    
    绘制内容:
    ┌─────────────────────────────────────────────┐
    │ 📌 标题文本...                    12:30     │
    │ [标签1] [标签2]                             │
    └─────────────────────────────────────────────┘
    
    使用示例:
        delegate = MemoDelegate()
        list_view.setItemDelegate(delegate)
    """
    
    # 尺寸常量
    ITEM_HEIGHT = 70
    PADDING = 12
    TAG_HEIGHT = 20
    TAG_PADDING = 8
    TAG_MARGIN = 6
    
    # 颜色主题 (深色)
    COLORS = {
        'background': QColor('#2d2d2d'),
        'background_hover': QColor('#3d3d3d'),
        'background_selected': QColor('#4a4a4a'),
        'title': QColor('#e0e0e0'),
        'time': QColor('#888888'),
        'tag_bg': QColor('#3a5a7c'),
        'tag_text': QColor('#ffffff'),
        'pin_icon': QColor('#ffd700'),
        'border': QColor('#404040'),
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 字体
        self._title_font = QFont("Microsoft YaHei", 11)
        self._title_font.setBold(True)
        self._time_font = QFont("Microsoft YaHei", 9)
        self._tag_font = QFont("Microsoft YaHei", 8)
    
    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        """
        绘制单个列表项
        
        性能关键: 使用 QPainter 直接绘制，比创建 QWidget 快 100x+
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = option.rect
        
        # 1. 绘制背景
        self._draw_background(painter, option, rect)
        
        # 2. 获取数据
        title = index.data(MemoListModel.TitleRole) or ""
        time_str = index.data(MemoListModel.RelativeTimeRole) or ""
        tags = index.data(MemoListModel.TagsRole) or []
        is_pinned = index.data(MemoListModel.IsPinnedRole) or False
        
        # 3. 绘制置顶图标
        x_offset = self.PADDING
        if is_pinned:
            x_offset = self._draw_pin_icon(painter, rect)
        
        # 4. 绘制时间 (右上角)
        time_width = self._draw_time(painter, rect, time_str)
        
        # 5. 绘制标题
        self._draw_title(painter, rect, title, x_offset, time_width)
        
        # 6. 绘制标签
        self._draw_tags(painter, rect, tags)
        
        # 7. 绘制底部分隔线
        self._draw_separator(painter, rect)
        
        painter.restore()
    
    def sizeHint(self, option, index: QModelIndex) -> QSize:
        """返回项目尺寸"""
        return QSize(option.rect.width(), self.ITEM_HEIGHT)
    
    # ========================================
    # 私有绘制方法
    # ========================================
    
    def _draw_background(self, painter: QPainter, option, rect: QRect) -> None:
        """绘制背景"""
        if option.state & QStyle.StateFlag.State_Selected:
            bg_color = self.COLORS['background_selected']
        elif option.state & QStyle.StateFlag.State_MouseOver:
            bg_color = self.COLORS['background_hover']
        else:
            bg_color = self.COLORS['background']
        
        painter.fillRect(rect, bg_color)
    
    def _draw_pin_icon(self, painter: QPainter, rect: QRect) -> int:
        """绘制置顶图标，返回新的 x 偏移"""
        painter.setFont(QFont("Segoe UI Emoji", 12))
        painter.setPen(self.COLORS['pin_icon'])
        
        icon_rect = QRect(
            rect.left() + self.PADDING,
            rect.top() + self.PADDING,
            20, 20
        )
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, "📌")
        
        return self.PADDING + 24
    
    def _draw_time(self, painter: QPainter, rect: QRect, time_str: str) -> int:
        """绘制时间，返回时间文本宽度"""
        painter.setFont(self._time_font)
        painter.setPen(self.COLORS['time'])
        
        fm = QFontMetrics(self._time_font)
        time_width = fm.horizontalAdvance(time_str)
        
        time_rect = QRect(
            rect.right() - self.PADDING - time_width,
            rect.top() + self.PADDING,
            time_width,
            20
        )
        painter.drawText(time_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, time_str)
        
        return time_width + self.PADDING * 2
    
    def _draw_title(self, painter: QPainter, rect: QRect, title: str, x_offset: int, time_width: int) -> None:
        """绘制标题"""
        painter.setFont(self._title_font)
        painter.setPen(self.COLORS['title'])
        
        available_width = rect.width() - x_offset - time_width
        
        # 文本省略
        fm = QFontMetrics(self._title_font)
        elided_title = fm.elidedText(title, Qt.TextElideMode.ElideRight, available_width)
        
        title_rect = QRect(
            rect.left() + x_offset,
            rect.top() + self.PADDING,
            available_width,
            24
        )
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
    
    def _draw_tags(self, painter: QPainter, rect: QRect, tags: list) -> None:
        """绘制标签胶囊"""
        if not tags:
            return
        
        painter.setFont(self._tag_font)
        fm = QFontMetrics(self._tag_font)
        
        x = rect.left() + self.PADDING
        y = rect.top() + self.PADDING + 28
        max_x = rect.right() - self.PADDING
        
        for tag in tags[:5]:  # 最多显示5个标签
            tag_text = f"#{tag}"
            text_width = fm.horizontalAdvance(tag_text)
            tag_width = text_width + self.TAG_PADDING * 2
            
            # 检查是否超出边界
            if x + tag_width > max_x:
                break
            
            # 绘制标签背景 (圆角矩形)
            tag_rect = QRect(x, y, tag_width, self.TAG_HEIGHT)
            painter.setBrush(QBrush(self.COLORS['tag_bg']))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tag_rect, 4, 4)
            
            # 绘制标签文字
            painter.setPen(self.COLORS['tag_text'])
            painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_text)
            
            x += tag_width + self.TAG_MARGIN
    
    def _draw_separator(self, painter: QPainter, rect: QRect) -> None:
        """绘制底部分隔线"""
        painter.setPen(QPen(self.COLORS['border'], 1))
        painter.drawLine(
            rect.left() + self.PADDING,
            rect.bottom(),
            rect.right() - self.PADDING,
            rect.bottom()
        )
