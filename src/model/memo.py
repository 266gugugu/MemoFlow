# src/model/memo.py
# -*- coding: utf-8 -*-
"""
Memo 数据类

v2.0 变更:
- 使用 Unix 时间戳 (int) 而非 ISO 字符串
- 添加 is_pinned 字段
- 移除 time_str，改用属性方法
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Memo:
    """
    备忘录数据模型
    
    Attributes:
        id: 数据库主键
        content: 备忘录内容 (支持 Markdown)
        created_at: 创建时间 (Unix 时间戳)
        is_pinned: 是否置顶
        tags: 标签列表
    """
    id: int
    content: str
    created_at: int
    is_pinned: bool = False
    tags: List[str] = field(default_factory=list)
    
    @property
    def title(self) -> str:
        """从 content 提取第一行作为标题（最多50字符）"""
        first_line = self.content.split('\n', 1)[0]
        return first_line[:50] if len(first_line) > 50 else first_line
    
    @property
    def time_str(self) -> str:
        """格式化时间显示 (HH:MM)"""
        return datetime.fromtimestamp(self.created_at).strftime("%H:%M")
    
    @property
    def date_str(self) -> str:
        """格式化日期显示 (YYYY-MM-DD)"""
        return datetime.fromtimestamp(self.created_at).strftime("%Y-%m-%d")
    
    @property
    def relative_time(self) -> str:
        """相对时间显示 (刚刚 / 5分钟前 / 昨天 / 2024-01-01)"""
        now = datetime.now()
        created = datetime.fromtimestamp(self.created_at)
        delta = now - created
        
        if delta.days == 0:
            if delta.seconds < 60:
                return "刚刚"
            elif delta.seconds < 3600:
                return f"{delta.seconds // 60}分钟前"
            else:
                return f"{delta.seconds // 3600}小时前"
        elif delta.days == 1:
            return "昨天"
        elif delta.days < 7:
            return f"{delta.days}天前"
        else:
            return self.date_str
    
    @classmethod
    def from_db_record(cls, record) -> 'Memo':
        """从数据库记录创建 Memo 实例"""
        return cls(
            id=record.id,
            content=record.content,
            created_at=record.created_at,
            is_pinned=record.is_pinned,
            tags=record.tags if record.tags else []
        )
