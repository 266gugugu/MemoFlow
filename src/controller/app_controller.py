# src/controller/app_controller.py
# -*- coding: utf-8 -*-
"""
应用控制器

职责:
- 连接 View 和 Model
- 协调数据库工作线程
- 实现搜索防抖 (Debounce)
- 管理应用生命周期
"""

import re
from typing import Optional
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.database.manager import DatabaseManager
from src.database.worker import DatabaseWorker
from src.model.memo import Memo
from src.model.memo_list_model import MemoListModel


class AppController(QObject):
    """
    MemoFlow 应用控制器
    
    信号:
        memos_loaded: 备忘录列表加载完成
        memo_added: 新备忘录添加成功
        memo_updated: 备忘录更新成功
        memo_deleted: 备忘录删除成功
        tags_updated: 标签列表更新
        error_occurred: 发生错误
    """
    
    # 信号定义
    memos_loaded = pyqtSignal()
    memo_added = pyqtSignal(int)       # memo_id
    memo_updated = pyqtSignal(int)     # memo_id
    memo_deleted = pyqtSignal(int)     # memo_id
    tags_updated = pyqtSignal(list)    # tag names
    error_occurred = pyqtSignal(str)   # error message
    
    # 防抖延迟 (毫秒)
    SEARCH_DEBOUNCE_MS = 300
    
    def __init__(self, db_path: str = None, parent=None):
        super().__init__(parent)
        
        # 数据库路径
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "memoflow.db"
        
        # 确保数据目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self._db = DatabaseManager(str(db_path))
        self._worker = DatabaseWorker(self._db)
        self._model = MemoListModel()
        
        # 搜索状态
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._execute_search)
        self._pending_search_query = ""
        self._current_tag_filter = None
        
        # 连接信号
        self._connect_signals()
        
        # 启动工作线程
        self._worker.start()
    
    def _connect_signals(self):
        """连接内部信号"""
        # 工作线程信号
        self._worker.memo_added.connect(self._on_memo_added)
        self._worker.memo_updated.connect(self._on_memo_updated)
        self._worker.memo_deleted.connect(self._on_memo_deleted)
        self._worker.pin_toggled.connect(self._on_pin_toggled)
        self._worker.error_occurred.connect(self._on_error)
    
    @property
    def model(self) -> MemoListModel:
        """获取列表模型（供 View 绑定）"""
        return self._model
    
    # ========================================
    # 数据加载
    # ========================================
    
    def load_memos(self, limit: int = 100) -> None:
        """加载备忘录列表"""
        records = self._db.get_all_memos(limit=limit)
        memos = [Memo.from_db_record(r) for r in records]
        self._model.setMemos(memos)
        self.memos_loaded.emit()
    
    def load_tags(self) -> None:
        """加载标签列表"""
        tags = self._db.get_all_tags()
        self.tags_updated.emit(tags)
    
    # ========================================
    # 搜索 (带防抖)
    # ========================================
    
    def search(self, query: str) -> None:
        """
        搜索备忘录 (防抖)
        
        输入后等待 300ms 无新输入才执行搜索，
        避免每次按键都触发数据库查询。
        """
        self._pending_search_query = query.strip()
        self._current_tag_filter = None
        self._search_timer.start(self.SEARCH_DEBOUNCE_MS)
    
    def _execute_search(self) -> None:
        """执行搜索"""
        query = self._pending_search_query
        
        if not query:
            self.load_memos()
            return
        
        records = self._db.search_memos(query)
        memos = [Memo.from_db_record(r) for r in records]
        self._model.setMemos(memos)
    
    def filter_by_tag(self, tag_name: str) -> None:
        """按标签筛选"""
        self._current_tag_filter = tag_name
        self._pending_search_query = ""
        
        if not tag_name:
            self.load_memos()
            return
        
        records = self._db.get_memos_by_tag(tag_name)
        memos = [Memo.from_db_record(r) for r in records]
        self._model.setMemos(memos)
    
    def clear_filter(self) -> None:
        """清除筛选"""
        self._current_tag_filter = None
        self._pending_search_query = ""
        self.load_memos()
    
    # ========================================
    # CRUD 操作
    # ========================================
    
    def add_memo(self, raw_text: str) -> None:
        """
        添加新备忘录
        
        支持 #标签 语法自动提取标签
        """
        # 提取标签
        tags = re.findall(r"#(\S+)", raw_text)
        content = re.sub(r"#\S+", "", raw_text).strip()
        
        if not content:
            content = "无标题备忘"
        
        self._worker.add_memo(content, tags)
    
    def update_memo(self, memo_id: int, content: str, tags: list = None) -> None:
        """更新备忘录"""
        self._worker.update_memo(memo_id, content=content, tags=tags)
    
    def delete_memo(self, memo_id: int) -> None:
        """删除备忘录"""
        self._worker.delete_memo(memo_id)
    
    def toggle_pin(self, memo_id: int) -> None:
        """切换置顶状态"""
        self._worker.toggle_pin(memo_id)
    
    # ========================================
    # 回调处理
    # ========================================
    
    def _on_memo_added(self, memo_id: int, callback_id: str) -> None:
        """备忘录添加完成回调"""
        # Reload to ensure correct order (pinned) and filtering
        if self._current_tag_filter:
            self.filter_by_tag(self._current_tag_filter)
        elif self._pending_search_query:
            self._execute_search()
        else:
            self.load_memos()
        
        self.memo_added.emit(memo_id)
        self.load_tags()  # 可能有新标签
    
    def _on_memo_updated(self, memo_id: int, callback_id: str) -> None:
        """备忘录更新完成回调"""
        record = self._db.get_memo_by_id(memo_id)
        if record:
            memo = Memo.from_db_record(record)
            self._model.updateMemo(memo_id, memo)
        
        self.memo_updated.emit(memo_id)
    
    def _on_memo_deleted(self, memo_id: int, callback_id: str) -> None:
        """备忘录删除完成回调"""
        self._model.removeMemo(memo_id)
        self.memo_deleted.emit(memo_id)
    
    def _on_pin_toggled(self, memo_id: int, callback_id: str) -> None:
        """置顶状态切换完成回调"""
        # 重新加载以正确排序
        if self._current_tag_filter:
            self.filter_by_tag(self._current_tag_filter)
        elif self._pending_search_query:
            self._execute_search()
        else:
            self.load_memos()
    
    def _on_error(self, error_msg: str, callback_id: str) -> None:
        """错误处理"""
        self.error_occurred.emit(error_msg)
    
    # ========================================
    # 生命周期
    # ========================================
    
    def shutdown(self) -> None:
        """关闭控制器，清理资源"""
        self._search_timer.stop()
        self._worker.stop()
        self._db.close()
