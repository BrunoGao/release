-- Migration: Update t_alert_rules.tenant_id to customer_id
-- Database: test, User: root/123456
-- Date: 2025-08-15

USE test;

-- Check current table structure
DESCRIBE t_alert_rules;

-- Check if tenant_id column exists
SET @col_exists = (SELECT COUNT(*) 
                   FROM information_schema.COLUMNS 
                   WHERE TABLE_SCHEMA = DATABASE() 
                   AND TABLE_NAME = 't_alert_rules' 
                   AND COLUMN_NAME = 'tenant_id');

-- Rename tenant_id to customer_id if it exists
SET @sql = IF(@col_exists > 0, 
              'ALTER TABLE t_alert_rules CHANGE COLUMN tenant_id customer_id BIGINT COMMENT "客户ID";', 
              'SELECT "tenant_id column not found, adding customer_id column" as message;');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- If tenant_id didn't exist, add customer_id column
SET @customer_col_exists = (SELECT COUNT(*) 
                           FROM information_schema.COLUMNS 
                           WHERE TABLE_SCHEMA = DATABASE() 
                           AND TABLE_NAME = 't_alert_rules' 
                           AND COLUMN_NAME = 'customer_id');

SET @sql2 = IF(@customer_col_exists = 0, 
               'ALTER TABLE t_alert_rules ADD COLUMN customer_id BIGINT COMMENT "客户ID";', 
               'SELECT "customer_id column already exists" as message;');

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- Verify the final structure
DESCRIBE t_alert_rules;