-- ============================================
-- AI圆桌讨论系统 - 数据库表结构
-- 版本: 1.0.0
-- 创建日期: 2026-06-26
-- ============================================

-- ============================================
-- 1. 讨论表 (discussions)
-- ============================================
CREATE TABLE IF NOT EXISTS discussions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK(length(title) > 0 AND length(title) <= 200),
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 索引：按状态查询
CREATE INDEX IF NOT EXISTS idx_discussions_status ON discussions(status);

-- 索引：按创建时间倒序查询（用于列表展示）
CREATE INDEX IF NOT EXISTS idx_discussions_created_at ON discussions(created_at DESC);

-- ============================================
-- 2. 参与者表 (participants) - AI专家
-- ============================================
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id INTEGER NOT NULL,
    name TEXT NOT NULL CHECK(length(name) > 0 AND length(name) <= 50),
    role TEXT NOT NULL CHECK(length(role) > 0 AND length(role) <= 100),
    expertise TEXT,
    system_prompt TEXT NOT NULL,
    avatar_color TEXT DEFAULT '#3B82F6',
    order_index INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE CASCADE
);

-- 索引：按讨论ID和顺序查询
CREATE INDEX IF NOT EXISTS idx_participants_discussion ON participants(discussion_id, order_index);

-- ============================================
-- 3. 消息表 (messages)
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    content TEXT NOT NULL CHECK(length(content) > 0),
    round_number INTEGER NOT NULL DEFAULT 1 CHECK(round_number > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
);

-- 索引：按讨论ID、轮次、时间查询（用于按顺序展示讨论）
CREATE INDEX IF NOT EXISTS idx_messages_discussion_round ON messages(discussion_id, round_number, created_at);

-- 索引：按参与者查询（统计专家发言）
CREATE INDEX IF NOT EXISTS idx_messages_participant ON messages(participant_id);

-- ============================================
-- 4. 共识表 (consensus)
-- ============================================
CREATE TABLE IF NOT EXISTS consensus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id INTEGER NOT NULL UNIQUE,
    summary TEXT NOT NULL CHECK(length(summary) > 0),
    key_points TEXT NOT NULL, -- JSON格式: ["要点1", "要点2", "要点3"]
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE CASCADE
);

-- 索引：按讨论ID查询
CREATE INDEX IF NOT EXISTS idx_consensus_discussion ON consensus(discussion_id);

-- ============================================
-- 5. 触发器：自动更新 updated_at
-- ============================================

-- 触发器：更新讨论表的 updated_at 字段
CREATE TRIGGER IF NOT EXISTS update_discussion_timestamp 
AFTER UPDATE ON discussions
FOR EACH ROW
BEGIN
    UPDATE discussions 
    SET updated_at = datetime('now', 'localtime') 
    WHERE id = NEW.id;
END;

-- 触发器：插入消息时更新讨论表的 updated_at
CREATE TRIGGER IF NOT EXISTS update_discussion_on_message 
AFTER INSERT ON messages
FOR EACH ROW
BEGIN
    UPDATE discussions 
    SET updated_at = datetime('now', 'localtime') 
    WHERE id = NEW.discussion_id;
END;

-- 触发器：插入共识时更新讨论状态为completed
CREATE TRIGGER IF NOT EXISTS update_discussion_on_consensus 
AFTER INSERT ON consensus
FOR EACH ROW
BEGIN
    UPDATE discussions 
    SET status = 'completed', 
        updated_at = datetime('now', 'localtime') 
    WHERE id = NEW.discussion_id;
END;

-- ============================================
-- 6. 初始化数据（可选）
-- ============================================

-- 插入示例讨论（仅用于开发测试）
-- INSERT INTO discussions (title, description, status) 
-- VALUES ('如何设计高并发系统', '讨论微服务架构下的高并发解决方案', 'completed');
