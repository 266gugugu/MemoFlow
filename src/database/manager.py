# src/database/manager.py
# -*- coding: utf-8 -*-
"""
线程安全的数据库管理器

设计要点:
- 使用 threading.local() 实现每线程独立连接
- 所有写操作通过 DatabaseWorker 在独立线程执行
- 读操作可直接在主线程调用
"""

import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MemoRecord:
    """数据库记录映射对象"""
    id: int
    content: str
    created_at: int
    is_pinned: bool
    tags: List[str]

    @property
    def title(self) -> str:
        """从 content 提取第一行作为标题（最多50字符）"""
        first_line = self.content.split('\n', 1)[0]
        return first_line[:50] if len(first_line) > 50 else first_line


class DatabaseManager:
    """
    MemoFlow 数据库管理器
    
    使用示例:
        db = DatabaseManager("path/to/memoflow.db")
        memos = db.get_all_memos()
        results = db.search_memos("关键词")
    """
    
    _local = threading.local()
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接（线程安全）"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.connection = conn
        return self._local.connection
    
    def _init_schema(self) -> None:
        """初始化数据库表结构"""
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            conn = self._get_connection()
            conn.executescript(schema_sql)
            conn.commit()
    
    # ========================================
    # 读操作 (可在主线程直接调用)
    # ========================================
    
    def get_all_memos(self, limit: int = 100, offset: int = 0) -> List[MemoRecord]:
        """
        获取所有备忘录（分页，置顶优先，按时间倒序）
        
        Args:
            limit: 每页数量
            offset: 偏移量
        
        Returns:
            MemoRecord 列表
        """
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT m.id, m.content, m.created_at, m.is_pinned,
                   GROUP_CONCAT(t.name, ',') as tags
            FROM memos m
            LEFT JOIN memo_tags mt ON m.id = mt.memo_id
            LEFT JOIN tags t ON mt.tag_id = t.id
            GROUP BY m.id
            ORDER BY m.is_pinned DESC, m.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        return [self._row_to_memo(row) for row in cursor.fetchall()]
    
    def get_memo_by_id(self, memo_id: int) -> Optional[MemoRecord]:
        """根据 ID 获取单条备忘录"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT m.id, m.content, m.created_at, m.is_pinned,
                   GROUP_CONCAT(t.name, ',') as tags
            FROM memos m
            LEFT JOIN memo_tags mt ON m.id = mt.memo_id
            LEFT JOIN tags t ON mt.tag_id = t.id
            WHERE m.id = ?
            GROUP BY m.id
        """, (memo_id,))
        
        row = cursor.fetchone()
        return self._row_to_memo(row) if row else None
    
    def search_memos(self, query: str, limit: int = 100) -> List[MemoRecord]:
        """
        使用 FTS5 全文搜索备忘录
        
        Args:
            query: 搜索关键词
            limit: 最大返回数量
        
        Returns:
            匹配的 MemoRecord 列表（按相关性排序）
        """
        if not query.strip():
            return self.get_all_memos(limit=limit)
        
        conn = self._get_connection()
        # 使用 FTS5 MATCH 语法，支持前缀匹配
        fts_query = f"{query}*"
        cursor = conn.execute("""
            SELECT m.id, m.content, m.created_at, m.is_pinned,
                   GROUP_CONCAT(t.name, ',') as tags
            FROM memos m
            INNER JOIN memos_fts ON m.id = memos_fts.rowid
            LEFT JOIN memo_tags mt ON m.id = mt.memo_id
            LEFT JOIN tags t ON mt.tag_id = t.id
            WHERE memos_fts MATCH ?
            GROUP BY m.id
            ORDER BY m.is_pinned DESC, rank
            LIMIT ?
        """, (fts_query, limit))
        
        return [self._row_to_memo(row) for row in cursor.fetchall()]
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签名称"""
        conn = self._get_connection()
        cursor = conn.execute("SELECT name FROM tags ORDER BY name")
        return [row['name'] for row in cursor.fetchall()]
    
    def get_memos_by_tag(self, tag_name: str, limit: int = 100) -> List[MemoRecord]:
        """根据标签筛选备忘录"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT m.id, m.content, m.created_at, m.is_pinned,
                   GROUP_CONCAT(t2.name, ',') as tags
            FROM memos m
            INNER JOIN memo_tags mt ON m.id = mt.memo_id
            INNER JOIN tags t ON mt.tag_id = t.id AND t.name = ?
            LEFT JOIN memo_tags mt2 ON m.id = mt2.memo_id
            LEFT JOIN tags t2 ON mt2.tag_id = t2.id
            GROUP BY m.id
            ORDER BY m.is_pinned DESC, m.created_at DESC
            LIMIT ?
        """, (tag_name, limit))
        
        return [self._row_to_memo(row) for row in cursor.fetchall()]
    
    def get_memo_count(self) -> int:
        """获取备忘录总数"""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM memos")
        return cursor.fetchone()[0]
    
    # ========================================
    # 写操作 (建议通过 DatabaseWorker 调用)
    # ========================================
    
    def add_memo(self, content: str, tags: List[str] = None, is_pinned: bool = False) -> int:
        """
        添加新备忘录
        
        Args:
            content: 备忘录内容
            tags: 标签列表
            is_pinned: 是否置顶
        
        Returns:
            新备忘录的 ID
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "INSERT INTO memos (content, is_pinned) VALUES (?, ?)",
            (content, int(is_pinned))
        )
        memo_id = cursor.lastrowid
        
        if tags:
            self._set_memo_tags(memo_id, tags)
        
        conn.commit()
        return memo_id
    
    def update_memo(self, memo_id: int, content: str = None, 
                    is_pinned: bool = None, tags: List[str] = None) -> bool:
        """
        更新备忘录
        
        Args:
            memo_id: 备忘录 ID
            content: 新内容 (None 表示不更新)
            is_pinned: 新置顶状态 (None 表示不更新)
            tags: 新标签列表 (None 表示不更新)
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        
        updates = []
        params = []
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if is_pinned is not None:
            updates.append("is_pinned = ?")
            params.append(int(is_pinned))
        
        if updates:
            params.append(memo_id)
            conn.execute(
                f"UPDATE memos SET {', '.join(updates)} WHERE id = ?",
                params
            )
        
        if tags is not None:
            self._set_memo_tags(memo_id, tags)
        
        conn.commit()
        return True
    
    def delete_memo(self, memo_id: int) -> bool:
        """删除备忘录"""
        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def toggle_pin(self, memo_id: int) -> bool:
        """切换置顶状态"""
        conn = self._get_connection()
        conn.execute(
            "UPDATE memos SET is_pinned = NOT is_pinned WHERE id = ?",
            (memo_id,)
        )
        conn.commit()
        return True
    
    # ========================================
    # 私有方法
    # ========================================
    
    def _set_memo_tags(self, memo_id: int, tags: List[str]) -> None:
        """设置备忘录的标签（先清空再添加）"""
        conn = self._get_connection()
        
        # 清空现有标签关联
        conn.execute("DELETE FROM memo_tags WHERE memo_id = ?", (memo_id,))
        
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            
            # 插入或获取标签 ID
            conn.execute(
                "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                (tag_name,)
            )
            cursor = conn.execute(
                "SELECT id FROM tags WHERE name = ?",
                (tag_name,)
            )
            tag_id = cursor.fetchone()['id']
            
            # 创建关联
            conn.execute(
                "INSERT OR IGNORE INTO memo_tags (memo_id, tag_id) VALUES (?, ?)",
                (memo_id, tag_id)
            )
    
    def _row_to_memo(self, row: sqlite3.Row) -> MemoRecord:
        """将数据库行转换为 MemoRecord"""
        tags_str = row['tags']
        tags = tags_str.split(',') if tags_str else []
        return MemoRecord(
            id=row['id'],
            content=row['content'],
            created_at=row['created_at'],
            is_pinned=bool(row['is_pinned']),
            tags=tags
        )
    
    def close(self) -> None:
        """关闭当前线程的连接"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
