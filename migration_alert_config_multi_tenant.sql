-- 告警配置多租户支持迁移脚本
-- Database: test, User: root/123456  
-- Date: 2025-08-27
-- Purpose: 为告警配置表添加多租户支持，统一使用customer_id字段

USE test;

-- 1. 为微信告警配置表添加customer_id字段（如果不存在）
ALTER TABLE `t_wechat_alarm_config` 
ADD COLUMN `customer_id` bigint DEFAULT NULL COMMENT '客户ID（多租户标识）' 
AFTER `tenant_id`;

-- 2. 更新现有数据：将tenant_id映射为customer_id
UPDATE `t_wechat_alarm_config` 
SET `customer_id` = `tenant_id` 
WHERE `customer_id` IS NULL;

-- 3. 为customer_id字段添加索引
ALTER TABLE `t_wechat_alarm_config` 
ADD INDEX `idx_customer_id` (`customer_id`);

-- 4. 创建消息配置表（如果不存在）
CREATE TABLE IF NOT EXISTS `t_message_config` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `customer_id` bigint NOT NULL COMMENT '客户ID（租户ID）',
  `name` varchar(100) NOT NULL COMMENT '配置名称',
  `type` varchar(20) NOT NULL COMMENT '消息类型: sms/email/webhook/internal',
  `endpoint` varchar(500) NOT NULL COMMENT '接收地址（手机号/邮箱/URL等）',
  `access_key` varchar(200) DEFAULT NULL COMMENT 'Access Key（短信服务密钥、SMTP服务器、请求方法等）',
  `secret_key` varchar(200) DEFAULT NULL COMMENT 'Secret Key（密码、Token等）',
  `template_id` varchar(100) DEFAULT NULL COMMENT '模板ID',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `description` text DEFAULT NULL COMMENT '备注描述',
  `create_user` varchar(64) DEFAULT NULL COMMENT '创建用户',
  `create_user_id` bigint DEFAULT NULL COMMENT '创建用户ID',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_user` varchar(64) DEFAULT NULL COMMENT '修改用户',
  `update_user_id` bigint DEFAULT NULL COMMENT '修改用户ID',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `is_deleted` tinyint unsigned DEFAULT '0' COMMENT '是否删除(0:否,1:是)',
  PRIMARY KEY (`id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_type` (`type`),
  KEY `idx_enabled` (`enabled`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='消息配置表';

-- 5. 插入消息配置示例数据
INSERT INTO `t_message_config` (
  `customer_id`, `name`, `type`, `endpoint`, `access_key`, `secret_key`, `template_id`, `enabled`, 
  `description`, `create_user`, `create_user_id`, `create_time`
) VALUES 
(1, '短信告警配置', 'sms', '13888888888', 'your_sms_access_key', 'your_sms_secret_key', 'SMS_123456', 1, '用于发送短信告警通知', 'system', 1, NOW()),
(1, '邮件告警配置', 'email', 'admin@example.com', 'smtp.example.com', 'your_email_password', NULL, 1, '用于发送邮件告警通知', 'system', 1, NOW()),
(1, 'Webhook告警配置', 'webhook', 'https://api.example.com/webhook', 'POST', 'your_webhook_token', NULL, 1, '用于发送Webhook告警通知', 'system', 1, NOW()),
(1, '站内消息配置', 'internal', 'internal', NULL, NULL, NULL, 1, '用于发送站内消息通知', 'system', 1, NOW())
ON DUPLICATE KEY UPDATE
  `update_time` = NOW();

-- 6. 插入微信告警配置示例数据（企业微信和公众号）
INSERT INTO `t_wechat_alarm_config` (
  `tenant_id`, `customer_id`, `type`, `corp_id`, `agent_id`, `secret`, `template_id`, `enabled`, 
  `create_user`, `create_user_id`, `create_time`
) VALUES (
  1, 1, 'enterprise', 'ww1234567890abcdef', '1000001', 'your_enterprise_secret_here', 'template_enterprise_001', 1,
  'system', 1, NOW()
) ON DUPLICATE KEY UPDATE
  `update_time` = NOW();

INSERT INTO `t_wechat_alarm_config` (
  `tenant_id`, `customer_id`, `type`, `appid`, `appsecret`, `template_id`, `enabled`, 
  `create_user`, `create_user_id`, `create_time`
) VALUES (
  1, 1, 'official', 'wx1234567890abcdef', 'your_official_secret_here', 'template_official_001', 1,
  'system', 1, NOW()
) ON DUPLICATE KEY UPDATE
  `update_time` = NOW();

-- 7. 验证迁移结果
SELECT '=== 迁移完成，验证结果 ===' as status;

SELECT 'WeChat配置表结构' as info;
DESCRIBE t_wechat_alarm_config;

SELECT 'WeChat配置数据统计' as info;
SELECT 
  customer_id,
  type,
  COUNT(*) as count,
  SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_count
FROM t_wechat_alarm_config 
WHERE is_deleted = 0 
GROUP BY customer_id, type;

SELECT 'Message配置表结构' as info;
DESCRIBE t_message_config;

SELECT 'Message配置数据统计' as info;
SELECT 
  customer_id,
  type,
  COUNT(*) as count,
  SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_count
FROM t_message_config 
WHERE is_deleted = 0 
GROUP BY customer_id, type;

SELECT '多租户告警配置迁移完成！' as final_status;