-- MemoFlow v2.0 Database Schema
-- SQLite with FTS5 Full-Text Search

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- ============================================================
-- 核心数据表
-- ============================================================

-- 主备忘录表
CREATE TABLE IF NOT EXISTS memos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    is_pinned INTEGER NOT NULL DEFAULT 0
);

-- 标签表 (唯一标签名)
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- 备忘录-标签 多对多关联表
CREATE TABLE IF NOT EXISTS memo_tags (
    memo_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (memo_id, tag_id),
    FOREIGN KEY (memo_id) REFERENCES memos(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- ============================================================
-- FTS5 全文搜索虚拟表 (毫秒级搜索)
-- ============================================================

-- 使用独立 FTS 表 (非外部内容表模式) 以避免列名冲突
-- FTS 表存储自己的数据副本，通过触发器同步
CREATE VIRTUAL TABLE IF NOT EXISTS memos_fts USING fts5(
    memo_content,
    tokenize='unicode61'
);

-- ============================================================
-- 触发器：保持 FTS 索引同步
-- ============================================================

-- INSERT 后同步到 FTS
CREATE TRIGGER IF NOT EXISTS memos_ai AFTER INSERT ON memos BEGIN
    INSERT INTO memos_fts(rowid, memo_content) VALUES (new.id, new.content);
END;

-- DELETE 后从 FTS 移除
CREATE TRIGGER IF NOT EXISTS memos_ad AFTER DELETE ON memos BEGIN
    DELETE FROM memos_fts WHERE rowid = old.id;
END;

-- UPDATE 后更新 FTS
CREATE TRIGGER IF NOT EXISTS memos_au AFTER UPDATE ON memos BEGIN
    UPDATE memos_fts SET memo_content = new.content WHERE rowid = old.id;
END;

-- ============================================================
-- 索引优化
-- ============================================================

-- 按创建时间倒序排列 (最新在前)
CREATE INDEX IF NOT EXISTS idx_memos_created_at ON memos(created_at DESC);

-- 置顶状态索引
CREATE INDEX IF NOT EXISTS idx_memos_is_pinned ON memos(is_pinned DESC);

-- 标签关联索引
CREATE INDEX IF NOT EXISTS idx_memo_tags_memo_id ON memo_tags(memo_id);
CREATE INDEX IF NOT EXISTS idx_memo_tags_tag_id ON memo_tags(tag_id);
