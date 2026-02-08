# scripts/performance_test.py
# -*- coding: utf-8 -*-
"""
性能测试脚本

测试内容:
1. 插入 10,000 条记录的耗时
2. 全量查询耗时
3. FTS5 搜索耗时
4. UI 渲染性能 (需要手动观察)

使用方法:
    python scripts/performance_test.py
"""

import sys
import time
import random
import string
from pathlib import Path

# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.manager import DatabaseManager


def random_content(min_len=50, max_len=200):
    """生成随机内容"""
    length = random.randint(min_len, max_len)
    words = [
        "备忘录", "记录", "想法", "待办", "笔记", "会议", "项目",
        "Python", "PyQt6", "数据库", "性能", "优化", "测试",
        "医学", "研究", "论文", "实验", "数据", "分析",
        "代码", "函数", "类", "模块", "架构", "设计"
    ]
    content = " ".join(random.choices(words, k=length // 4))
    return content[:length]


def random_tags():
    """生成随机标签"""
    all_tags = ["工作", "学习", "生活", "重要", "待办", "已完成", 
                "Python", "医学", "研究", "项目", "会议", "笔记"]
    count = random.randint(0, 3)
    return random.sample(all_tags, count)


def test_insert_performance(db: DatabaseManager, count: int = 10000):
    """测试插入性能"""
    print(f"\n📊 测试插入 {count:,} 条记录...")
    
    # 使用直接 SQL 插入，批量提交以提高性能
    conn = db._get_connection()
    
    start = time.perf_counter()
    
    for i in range(count):
        content = random_content()
        tags = random_tags()
        
        # 直接插入，不单独提交
        cursor = conn.execute(
            "INSERT INTO memos (content, is_pinned) VALUES (?, ?)",
            (content, 0)
        )
        memo_id = cursor.lastrowid
        
        # FTS 触发器会自动同步
        
        # 每 500 条提交一次
        if (i + 1) % 500 == 0:
            conn.commit()
            elapsed = time.perf_counter() - start
            rate = (i + 1) / elapsed
            print(f"   已插入 {i + 1:,} 条 ({rate:.0f} 条/秒)")
    
    # 最终提交
    conn.commit()
    
    elapsed = time.perf_counter() - start
    rate = count / elapsed
    
    print(f"   ✅ 完成: {elapsed:.2f} 秒 ({rate:.0f} 条/秒)")
    return elapsed


def test_query_performance(db: DatabaseManager):
    """测试查询性能"""
    print("\n📊 测试查询性能...")
    
    # 测试全量查询
    start = time.perf_counter()
    memos = db.get_all_memos(limit=10000)
    elapsed = time.perf_counter() - start
    print(f"   全量查询 {len(memos):,} 条: {elapsed*1000:.2f} ms")
    
    # 测试分页查询
    start = time.perf_counter()
    memos = db.get_all_memos(limit=100, offset=0)
    elapsed = time.perf_counter() - start
    print(f"   分页查询 (100条): {elapsed*1000:.2f} ms")
    
    return elapsed


def test_search_performance(db: DatabaseManager):
    """测试 FTS5 搜索性能"""
    print("\n📊 测试 FTS5 搜索性能...")
    
    queries = ["Python", "医学", "项目会议", "待办重要", "研究数据分析"]
    
    for query in queries:
        start = time.perf_counter()
        results = db.search_memos(query, limit=100)
        elapsed = time.perf_counter() - start
        print(f"   搜索 '{query}': {len(results)} 条, {elapsed*1000:.2f} ms")
    
    return elapsed


def test_count_performance(db: DatabaseManager):
    """测试计数性能"""
    print("\n📊 测试计数性能...")
    
    start = time.perf_counter()
    count = db.get_memo_count()
    elapsed = time.perf_counter() - start
    print(f"   总记录数 {count:,}: {elapsed*1000:.2f} ms")
    
    return elapsed


def main():
    print("=" * 50)
    print("   MemoFlow v2.0 性能测试")
    print("=" * 50)
    
    # 使用临时数据库
    db_path = PROJECT_ROOT / "data" / "performance_test.db"
    
    # 清理旧测试数据
    if db_path.exists():
        db_path.unlink()
    
    print(f"\n📁 测试数据库: {db_path}")
    
    db = DatabaseManager(str(db_path))
    
    try:
        # 运行测试
        test_insert_performance(db, count=10000)
        test_query_performance(db)
        test_search_performance(db)
        test_count_performance(db)
        
        print("\n" + "=" * 50)
        print("   测试完成!")
        print("=" * 50)
        
        # 性能总结
        print("\n📋 性能总结:")
        print("   - 插入: 应达到 1000+ 条/秒")
        print("   - 分页查询: 应 < 10 ms")
        print("   - FTS5 搜索: 应 < 50 ms")
        print("   - UI 渲染: 请手动运行 main.py 观察滚动流畅度")
        
    finally:
        db.close()
        
        # 可选: 删除测试数据库
        # if db_path.exists():
        #     db_path.unlink()
        #     print(f"\n🗑️ 已删除测试数据库")


if __name__ == "__main__":
    main()
