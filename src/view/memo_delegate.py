# src/view/memo_delegate.py
# -*- coding: utf-8 -*-
"""
备忘录列表项委托 (高性能渲染) - Unifed Theme Version
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import QSize, QRect, Qt, QModelIndex, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontMetrics, QLinearGradient, QPainterPath

from src.model.memo_list_model import MemoListModel
from src.core.theme import AppTheme


class MemoDelegate(QStyledItemDelegate):
    """
    高性能备忘录项绘制委托
    
    Style: Modern Dark Card
    """
    
    # 尺寸常量
    ITEM_HEIGHT = 86          # 增加高度以适应卡片布局
    H_PADDING = 16            # 水平内边距
    V_PADDING = 12            # 垂直内边距
    TAG_HEIGHT = 22           # 标签高度
    TAG_PADDING = 10          # 标签水平内边距
    TAG_MARGIN = 8            # 标签间距
    CARD_MARGIN = 6           # 卡片外边距
    RADIUS = 10               # 圆角半径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 字体 - 使用更现代的字体栈
        self._title_font = QFont("Segoe UI", 11)
        self._title_font.setBold(True)
        
        self._content_font = QFont("Segoe UI", 10)
        
        self._time_font = QFont("Segoe UI", 9)
        
        self._tag_font = QFont("Segoe UI", 9)
    
    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        """绘制单个列表项 (卡片风格)"""
        if not index.isValid():
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取颜色
        c = AppTheme.COLORS
        
        # 计算卡片区域 (留出外边距)
        rect = option.rect
        card_rect = rect.adjusted(self.CARD_MARGIN, self.CARD_MARGIN // 2, -self.CARD_MARGIN, -self.CARD_MARGIN // 2)
        
        # 1. 绘制卡片背景
        self._draw_card_background(painter, option, card_rect, c)
        
        # 2. 获取数据
        title = index.data(MemoListModel.TitleRole) or ""
        time_str = index.data(MemoListModel.RelativeTimeRole) or ""
        tags = index.data(MemoListModel.TagsRole) or []
        is_pinned = index.data(MemoListModel.IsPinnedRole) or False
        
        # 内部内容区域
        content_rect = card_rect.adjusted(self.H_PADDING, self.V_PADDING, -self.H_PADDING, -self.V_PADDING)
        
        # 3. 绘制置顶图标
        title_x = content_rect.left()
        if is_pinned:
            title_x = self._draw_pin_icon(painter, content_rect, c)
        
        # 4. 绘制时间 (右上角)
        time_width = self._draw_time(painter, content_rect, time_str, c)
        
        # 5. 绘制标题
        self._draw_title(painter, content_rect, title, title_x, time_width, c)
        
        # 6. 绘制标签 (底部)
        self._draw_tags(painter, content_rect, tags, c)
        
        painter.restore()
    
    def sizeHint(self, option, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), self.ITEM_HEIGHT)
    
    # ========================================
    # 绘制辅助
    # ========================================
    
    def _draw_card_background(self, painter: QPainter, option, rect: QRect, c: dict) -> None:
        bg_color = QColor(c['bg_primary']) # 默认背景 (透明/与底色一致)
        border_color = QColor(c['border'])
        
        # 状态判断
        if option.state & QStyle.StateFlag.State_Selected:
            bg_color = QColor(c['bg_selected'])
            border_color = QColor(c['accent'])
        elif option.state & QStyle.StateFlag.State_MouseOver:
            bg_color = QColor(c['bg_hover'])
            border_color = QColor(c['text_tertiary'])
        else:
             # 普通状态：淡淡的分割线或者微弱背景
             bg_color = QColor(c['bg_secondary']) # 卡片背景略亮于主背景
             border_color = QColor(c['border'])
        
        # 绘制圆角矩形背景
        path = QPainterPath()
        path.addRoundedRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height()), self.RADIUS, self.RADIUS) # type: ignore
        
        painter.fillPath(path, bg_color)
        
        # 绘制边框
        pen = QPen(border_color, 1)
        if option.state & QStyle.StateFlag.State_Selected:
            pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)

    def _draw_pin_icon(self, painter: QPainter, rect: QRect, c: dict) -> int:
        font = QFont("Segoe UI Emoji", 10)
        painter.setFont(font)
        painter.setPen(QColor(c['warning'])) # 使用 warning 色作为置顶色 (Gold/Yellow)
        
        # 垂直居中于标题行 (假设标题行高约 24)
        icon_rect = QRect(rect.left(), rect.top(), 20, 24)
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "📌")
        
        return rect.left() + 24
    
    def _draw_time(self, painter: QPainter, rect: QRect, time_str: str, c: dict) -> int:
        painter.setFont(self._time_font)
        painter.setPen(QColor(c['text_tertiary']))
        
        fm = QFontMetrics(self._time_font)
        width = fm.horizontalAdvance(time_str)
        
        # 右上角
        time_rect = QRect(rect.right() - width, rect.top(), width, 24)
        painter.drawText(time_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, time_str)
        
        return width + 10 # 返回宽度 + 间距
    
    def _draw_title(self, painter: QPainter, rect: QRect, title: str, x: int, right_padding: int, c: dict) -> None:
        painter.setFont(self._title_font)
        painter.setPen(QColor(c['text_primary']))
        
        # 计算可用宽度
        width = rect.right() - x - right_padding
        if width <= 0: return
        
        fm = QFontMetrics(self._title_font)
        elided = fm.elidedText(title, Qt.TextElideMode.ElideRight, width)
        
        # 标题区域
        title_rect = QRect(x, rect.top(), width, 24)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

    def _draw_tags(self, painter: QPainter, rect: QRect, tags: list, c: dict) -> None:
        if not tags:
            return
            
        painter.setFont(self._tag_font)
        fm = QFontMetrics(self._tag_font)
        
        # 标签起始位置 (底部)
        x = rect.left()
        y = rect.bottom() - self.TAG_HEIGHT + 2 
        
        for tag in tags[:4]: # 限制数量
            text = f"#{tag}"
            w = fm.horizontalAdvance(text) + self.TAG_PADDING * 2
            
            # 边界检查
            if x + w > rect.right():
                break
                
            # 绘制胶囊背景
            tag_rect = QRect(x, y, w, self.TAG_HEIGHT)
            
            painter.setBrush(QBrush(QColor(c['tag_bg'])))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tag_rect, 10, 10) # 完全圆角
            
            # 绘制文字
            painter.setPen(QColor(c['tag_text']))
            painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, text)
            
            x += w + self.TAG_MARGIN
