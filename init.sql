
-- ============================================
-- 教研AI Agent 数据库初始化脚本 (MariaDB/MySQL)
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS tkben_api 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE tkben_api;

-- ============================================
-- 1. workshop_sessions - 教研会话表
-- ============================================
CREATE TABLE IF NOT EXISTS workshop_sessions (
    session_id VARCHAR(64) PRIMARY KEY COMMENT '会话ID',
    user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
    teacher_name VARCHAR(100) DEFAULT '老师' COMMENT '教师姓名',
    lesson_info JSON COMMENT '课例信息',
    report_summary TEXT COMMENT '课堂观察报告',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_active TINYINT DEFAULT 1 COMMENT '是否活跃(1活跃/0已结束)',
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教研会话表';

-- ============================================
-- 2. dialogue_records - 对话历史表
-- ============================================
CREATE TABLE IF NOT EXISTS dialogue_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    role VARCHAR(32) NOT NULL COMMENT '角色(user/peer/expert/mentor)',
    role_name VARCHAR(100) COMMENT '角色名称',
    content TEXT NOT NULL COMMENT '消息内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_session_id (session_id),
    CONSTRAINT fk_dialogue_session FOREIGN KEY (session_id) 
        REFERENCES workshop_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话历史表';

-- ============================================
-- 3. discussion_reports - 研讨报告表
-- ============================================
CREATE TABLE IF NOT EXISTS discussion_reports (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '报告ID',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    report_content TEXT NOT NULL COMMENT '研讨报告内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_session_id (session_id),
    CONSTRAINT fk_report_session FOREIGN KEY (session_id) 
        REFERENCES workshop_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='研讨报告表';

-- ============================================
-- 完成提示
-- ============================================
SELECT '数据库表结构创建完成！' AS message;

