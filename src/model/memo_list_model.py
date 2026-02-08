# src/model/memo_list_model.py
# -*- coding: utf-8 -*-
"""
高性能备忘录列表模型

核心设计:
- 继承 QAbstractListModel 实现虚拟列表
- QListView 只渲染可见区域，10,000 条记录和 100 条记录性能一致
- 通过自定义 Role 提供数据给 MemoDelegate
"""

from typing import List, Any, Optional
from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal


class MemoListModel(QAbstractListModel):
    """
    MemoFlow v2.0 核心列表模型
    
    使用示例:
        model = MemoListModel()
        model.setMemos(memos)  # 批量设置
        
        list_view = QListView()
        list_view.setModel(model)
        list_view.setItemDelegate(MemoDelegate())
    
    自定义角色:
        TitleRole: 标题文本
        ContentRole: 完整内容
        TimeRole: 格式化时间
        TagsRole: 标签列表
        IsPinnedRole: 是否置顶
        MemoIdRole: 数据库 ID
    """
    
    # 自定义数据角色
    TitleRole = Qt.ItemDataRole.UserRole + 1
    ContentRole = Qt.ItemDataRole.UserRole + 2
    TimeRole = Qt.ItemDataRole.UserRole + 3
    TagsRole = Qt.ItemDataRole.UserRole + 4
    IsPinnedRole = Qt.ItemDataRole.UserRole + 5
    MemoIdRole = Qt.ItemDataRole.UserRole + 6
    RelativeTimeRole = Qt.ItemDataRole.UserRole + 7
    
    # 自定义信号
    dataLoaded = pyqtSignal(int)  # 数据加载完成，参数为数量
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._memos: List = []  # List[Memo]
    
    # ========================================
    # QAbstractListModel 必须重写的方法
    # ========================================
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        返回列表行数
        
        QListView 会调用此方法确定需要渲染多少行。
        但实际只会渲染可见区域的行。
        """
        if parent.isValid():
            return 0
        return len(self._memos)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        根据角色返回对应数据
        
        QListView 和 MemoDelegate 会调用此方法获取每行数据。
        通过不同的 role 参数获取不同类型的数据。
        """
        if not index.isValid():
            return None
        
        row = index.row()
        if not (0 <= row < len(self._memos)):
            return None
        
        memo = self._memos[row]
        
        # 标准角色
        if role == Qt.ItemDataRole.DisplayRole:
            return memo.title
        
        # 自定义角色
        if role == self.TitleRole:
            return memo.title
        elif role == self.ContentRole:
            return memo.content
        elif role == self.TimeRole:
            return memo.time_str
        elif role == self.TagsRole:
            return memo.tags
        elif role == self.IsPinnedRole:
            return memo.is_pinned
        elif role == self.MemoIdRole:
            return memo.id
        elif role == self.RelativeTimeRole:
            return memo.relative_time
        
        return None
    
    def roleNames(self) -> dict:
        """返回角色名称映射（用于 QML，Python 中可选）"""
        roles = super().roleNames()
        roles[self.TitleRole] = b'title'
        roles[self.ContentRole] = b'content'
        roles[self.TimeRole] = b'time'
        roles[self.TagsRole] = b'tags'
        roles[self.IsPinnedRole] = b'isPinned'
        roles[self.MemoIdRole] = b'memoId'
        roles[self.RelativeTimeRole] = b'relativeTime'
        return roles
    
    # ========================================
    # 数据操作方法
    # ========================================
    
    def setMemos(self, memos: List) -> None:
        """
        批量设置数据（用于初始化或搜索结果）
        
        使用 beginResetModel/endResetModel 通知 View 完全重绘。
        比逐条插入更高效。
        """
        self.beginResetModel()
        self._memos = list(memos)
        self.endResetModel()
        self.dataLoaded.emit(len(self._memos))
    
    def addMemo(self, memo) -> None:
        """
        添加单条备忘录到顶部
        
        使用 beginInsertRows/endInsertRows 通知 View 局部更新。
        """
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._memos.insert(0, memo)
        self.endInsertRows()
    
    def removeMemo(self, memo_id: int) -> bool:
        """根据 ID 删除备忘录"""
        for i, memo in enumerate(self._memos):
            if memo.id == memo_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                del self._memos[i]
                self.endRemoveRows()
                return True
        return False
    
    def updateMemo(self, memo_id: int, new_memo) -> bool:
        """更新指定备忘录"""
        for i, memo in enumerate(self._memos):
            if memo.id == memo_id:
                self._memos[i] = new_memo
                index = self.index(i)
                self.dataChanged.emit(index, index)
                return True
        return False
    
    def getMemo(self, row: int) -> Optional[Any]:
        """根据行号获取 Memo 对象"""
        if 0 <= row < len(self._memos):
            return self._memos[row]
        return None
    
    def getMemoById(self, memo_id: int) -> Optional[Any]:
        """根据 ID 获取 Memo 对象"""
        for memo in self._memos:
            if memo.id == memo_id:
                return memo
        return None
    
    def getRowById(self, memo_id: int) -> int:
        """根据 ID 获取行号，不存在返回 -1"""
        for i, memo in enumerate(self._memos):
            if memo.id == memo_id:
                return i
        return -1
    
    def clear(self) -> None:
        """清空所有数据"""
        self.beginResetModel()
        self._memos.clear()
        self.endResetModel()
    
    @property
    def memos(self) -> List:
        """获取内部数据列表（只读）"""
        return self._memos.copy()
    
    def __len__(self) -> int:
        return len(self._memos)
