-- Migration: Remove duplicate notification_type column from t_alert_rules
-- Database: test, User: root/123456
-- Date: 2025-08-15

USE test;

-- Check current table structure
DESCRIBE t_alert_rules;

-- Remove duplicate notification_type column if exists
-- Keep only one notification_type column
ALTER TABLE t_alert_rules DROP COLUMN IF EXISTS notification_type;

-- Add back a single notification_type column with proper definition
ALTER TABLE t_alert_rules ADD COLUMN notification_type VARCHAR(50) DEFAULT 'message' COMMENT '通知方式: wechat/message/both';

-- Verify the final structure
DESCRIBE t_alert_rules;