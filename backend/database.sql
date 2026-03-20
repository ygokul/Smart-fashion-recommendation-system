-- UAI Chat Database Schema
-- Run this script before starting the application

CREATE DATABASE IF NOT EXISTS uai_chat_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE uai_chat_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    session_name VARCHAR(100) DEFAULT 'New Chat',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_last_activity (last_activity),
    UNIQUE KEY unique_user_session (user_id, session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(255) NOT NULL,
    user_id INT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT,
    tokens INT DEFAULT 0,
    image_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- User statistics table
CREATE TABLE IF NOT EXISTS user_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    total_messages INT DEFAULT 0,
    total_images INT DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    total_sessions INT DEFAULT 1,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_last_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Images table (for storing image metadata)
CREATE TABLE IF NOT EXISTS images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    image_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INT NULL,
    prompt TEXT,
    filename VARCHAR(255),
    url VARCHAR(500),
    model VARCHAR(100),
    size VARCHAR(50),
    format VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_image_id (image_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default admin user (password: admin123)
INSERT IGNORE INTO users (username, email, password_hash, subscription_tier, is_active) 
VALUES (
    'admin', 
    'admin@example.com', 
    '$2b$12$LQv3c1yqBWVHxkdwHpQftuMYW.8pN.VAqNk4HlMkQY9pN7J8Jq8XK', -- bcrypt hash for 'admin123'
    'premium', 
    TRUE
);

-- Insert statistics for admin
INSERT IGNORE INTO user_statistics (user_id) 
VALUES (1);

-- Create indexes for better performance
CREATE INDEX idx_chat_messages_session_user ON chat_messages(session_id, user_id);
CREATE INDEX idx_chat_messages_created_session ON chat_messages(created_at, session_id);
CREATE INDEX idx_user_sessions_user_activity ON user_sessions(user_id, last_activity);

-- Create views for easier queries
CREATE OR REPLACE VIEW user_chat_summary AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(DISTINCT us.session_id) as total_sessions,
    COUNT(cm.id) as total_messages,
    SUM(cm.tokens) as total_tokens,
    MAX(cm.created_at) as last_chat_activity
FROM users u
LEFT JOIN user_sessions us ON u.id = us.user_id
LEFT JOIN chat_messages cm ON us.session_id = cm.session_id AND cm.user_id = u.id
GROUP BY u.id, u.username;

CREATE OR REPLACE VIEW session_overview AS
SELECT 
    us.session_id,
    us.user_id,
    u.username,
    us.session_name,
    COUNT(cm.id) as message_count,
    MIN(cm.created_at) as session_start,
    MAX(cm.created_at) as session_end,
    TIMESTAMPDIFF(MINUTE, MIN(cm.created_at), MAX(cm.created_at)) as session_duration_minutes
FROM user_sessions us
LEFT JOIN users u ON us.user_id = u.id
LEFT JOIN chat_messages cm ON us.session_id = cm.session_id
GROUP BY us.session_id, us.user_id, u.username, us.session_name;

-- Grant permissions (adjust as needed for your setup)
-- CREATE USER IF NOT EXISTS 'uai_user'@'localhost' IDENTIFIED BY 'uai_password';
-- GRANT ALL PRIVILEGES ON uai_chat_db.* TO 'uai_user'@'localhost';
-- FLUSH PRIVILEGES;

-- Show table status
SHOW TABLES;

-- Show row counts
SELECT 
    'users' as table_name, 
    COUNT(*) as row_count 
FROM users
UNION ALL
SELECT 
    'user_sessions', 
    COUNT(*) 
FROM user_sessions
UNION ALL
SELECT 
    'chat_messages', 
    COUNT(*) 
FROM chat_messages
UNION ALL
SELECT 
    'user_statistics', 
    COUNT(*) 
FROM user_statistics
UNION ALL
SELECT 
    'images', 
    COUNT(*) 
FROM images;