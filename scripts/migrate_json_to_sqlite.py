# scripts/migrate_json_to_sqlite.py
# -*- coding: utf-8 -*-
"""
数据迁移脚本：memos.json → SQLite

使用方法:
    python scripts/migrate_json_to_sqlite.py

注意:
    - 会读取项目根目录的 memos.json
    - 会创建 data/memoflow.db
    - 运行前请备份 memos.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.manager import DatabaseManager


def parse_iso_to_timestamp(iso_str: str) -> int:
    """将 ISO 时间字符串转换为 Unix 时间戳"""
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return int(dt.timestamp())
    except:
        return int(datetime.now().timestamp())


def migrate():
    """执行迁移"""
    json_path = PROJECT_ROOT / "memos.json"
    db_path = PROJECT_ROOT / "data" / "memoflow.db"
    
    # 检查 JSON 文件
    if not json_path.exists():
        print(f"❌ 未找到 {json_path}")
        return False
    
    # 读取 JSON 数据
    print(f"📖 读取 {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        memos_data = json.load(f)
    
    print(f"   找到 {len(memos_data)} 条备忘录")
    
    # 初始化数据库
    print(f"🗄️ 初始化数据库 {db_path}...")
    db = DatabaseManager(str(db_path))
    
    # 迁移数据
    print("📦 迁移数据...")
    success_count = 0
    error_count = 0
    
    for memo in memos_data:
        try:
            # 提取字段
            content = memo.get("content", memo.get("title", ""))
            tags = memo.get("tags", [])
            created_at_str = memo.get("created_at", "")
            
            # 转换时间戳
            if created_at_str:
                created_at = parse_iso_to_timestamp(created_at_str)
            else:
                created_at = int(datetime.now().timestamp())
            
            # 插入数据库
            conn = db._get_connection()
            cursor = conn.execute(
                "INSERT INTO memos (content, created_at, is_pinned) VALUES (?, ?, ?)",
                (content, created_at, 0)
            )
            memo_id = cursor.lastrowid
            
            # 添加标签
            if tags:
                db._set_memo_tags(memo_id, tags)
            
            conn.commit()
            success_count += 1
            
        except Exception as e:
            print(f"   ⚠️ 迁移失败: {memo.get('title', '无标题')[:20]}... - {e}")
            error_count += 1
    
    # 完成
    print()
    print("=" * 40)
    print(f"✅ 迁移完成!")
    print(f"   成功: {success_count} 条")
    print(f"   失败: {error_count} 条")
    print(f"   数据库: {db_path}")
    print("=" * 40)
    
    db.close()
    return True


if __name__ == "__main__":
    migrate()
