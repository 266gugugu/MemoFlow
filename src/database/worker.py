# src/database/worker.py
# -*- coding: utf-8 -*-
"""
数据库工作线程

设计要点:
- 所有写操作在独立 QThread 中执行，避免阻塞 UI
- 通过 PyQt Signal 与主线程通信
- 使用任务队列支持批量操作
"""

from typing import List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum, auto
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition


class TaskType(Enum):
    """数据库任务类型"""
    ADD_MEMO = auto()
    UPDATE_MEMO = auto()
    DELETE_MEMO = auto()
    TOGGLE_PIN = auto()


@dataclass
class DatabaseTask:
    """数据库任务封装"""
    task_type: TaskType
    params: dict
    callback_id: Optional[str] = None


class DatabaseWorker(QThread):
    """
    数据库工作线程
    
    将写操作从主线程分离，确保 UI 流畅
    
    信号:
        memo_added: 备忘录添加完成，参数 (memo_id, callback_id)
        memo_updated: 备忘录更新完成，参数 (memo_id, callback_id)
        memo_deleted: 备忘录删除完成，参数 (memo_id, callback_id)
        error_occurred: 操作出错，参数 (error_message, callback_id)
    
    使用示例:
        worker = DatabaseWorker(db_manager)
        worker.memo_added.connect(on_memo_added)
        worker.start()
        
        worker.add_memo("新备忘录内容", ["标签1", "标签2"])
    """
    
    # 操作完成信号
    memo_added = pyqtSignal(int, str)      # (memo_id, callback_id)
    memo_updated = pyqtSignal(int, str)    # (memo_id, callback_id)
    memo_deleted = pyqtSignal(int, str)    # (memo_id, callback_id)
    pin_toggled = pyqtSignal(int, str)     # (memo_id, callback_id)
    error_occurred = pyqtSignal(str, str)  # (error_message, callback_id)
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self._db = db_manager
        self._tasks: List[DatabaseTask] = []
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._running = True
        self._task_counter = 0
    
    def run(self):
        """工作线程主循环"""
        while self._running:
            self._mutex.lock()
            while not self._tasks and self._running:
                self._condition.wait(self._mutex)
            
            if not self._running:
                self._mutex.unlock()
                break
            
            task = self._tasks.pop(0)
            self._mutex.unlock()
            
            self._execute_task(task)
    
    def _execute_task(self, task: DatabaseTask):
        """执行单个任务"""
        try:
            if task.task_type == TaskType.ADD_MEMO:
                memo_id = self._db.add_memo(
                    content=task.params.get('content', ''),
                    tags=task.params.get('tags', []),
                    is_pinned=task.params.get('is_pinned', False)
                )
                self.memo_added.emit(memo_id, task.callback_id or '')
            
            elif task.task_type == TaskType.UPDATE_MEMO:
                self._db.update_memo(
                    memo_id=task.params['memo_id'],
                    content=task.params.get('content'),
                    is_pinned=task.params.get('is_pinned'),
                    tags=task.params.get('tags')
                )
                self.memo_updated.emit(task.params['memo_id'], task.callback_id or '')
            
            elif task.task_type == TaskType.DELETE_MEMO:
                self._db.delete_memo(task.params['memo_id'])
                self.memo_deleted.emit(task.params['memo_id'], task.callback_id or '')
            
            elif task.task_type == TaskType.TOGGLE_PIN:
                self._db.toggle_pin(task.params['memo_id'])
                self.pin_toggled.emit(task.params['memo_id'], task.callback_id or '')
        
        except Exception as e:
            self.error_occurred.emit(str(e), task.callback_id or '')
    
    def _add_task(self, task: DatabaseTask):
        """添加任务到队列"""
        self._mutex.lock()
        self._tasks.append(task)
        self._condition.wakeOne()
        self._mutex.unlock()
    
    def _generate_callback_id(self) -> str:
        """生成唯一回调 ID"""
        self._task_counter += 1
        return f"task_{self._task_counter}"
    
    # ========================================
    # 公开 API
    # ========================================
    
    def add_memo(self, content: str, tags: List[str] = None, 
                 is_pinned: bool = False, callback_id: str = None) -> str:
        """
        添加备忘录（异步）
        
        Args:
            content: 内容
            tags: 标签列表
            is_pinned: 是否置顶
            callback_id: 可选的回调 ID，用于追踪操作
        
        Returns:
            回调 ID
        """
        callback_id = callback_id or self._generate_callback_id()
        task = DatabaseTask(
            task_type=TaskType.ADD_MEMO,
            params={
                'content': content,
                'tags': tags or [],
                'is_pinned': is_pinned
            },
            callback_id=callback_id
        )
        self._add_task(task)
        return callback_id
    
    def update_memo(self, memo_id: int, content: str = None,
                    is_pinned: bool = None, tags: List[str] = None,
                    callback_id: str = None) -> str:
        """更新备忘录（异步）"""
        callback_id = callback_id or self._generate_callback_id()
        task = DatabaseTask(
            task_type=TaskType.UPDATE_MEMO,
            params={
                'memo_id': memo_id,
                'content': content,
                'is_pinned': is_pinned,
                'tags': tags
            },
            callback_id=callback_id
        )
        self._add_task(task)
        return callback_id
    
    def delete_memo(self, memo_id: int, callback_id: str = None) -> str:
        """删除备忘录（异步）"""
        callback_id = callback_id or self._generate_callback_id()
        task = DatabaseTask(
            task_type=TaskType.DELETE_MEMO,
            params={'memo_id': memo_id},
            callback_id=callback_id
        )
        self._add_task(task)
        return callback_id
    
    def toggle_pin(self, memo_id: int, callback_id: str = None) -> str:
        """切换置顶状态（异步）"""
        callback_id = callback_id or self._generate_callback_id()
        task = DatabaseTask(
            task_type=TaskType.TOGGLE_PIN,
            params={'memo_id': memo_id},
            callback_id=callback_id
        )
        self._add_task(task)
        return callback_id
    
    def stop(self):
        """停止工作线程"""
        self._mutex.lock()
        self._running = False
        self._condition.wakeOne()
        self._mutex.unlock()
        self.wait()
