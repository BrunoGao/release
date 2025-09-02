-- 组织架构闭包表优化方案
-- 创建时间: 2025-08-30
-- 作者: bruno.gao
-- 功能: 提供高效的组织层级查询，支持租户隔离

-- 1. 组织闭包关系表 (核心优化表)
CREATE TABLE IF NOT EXISTS `sys_org_closure` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `ancestor_id` BIGINT NOT NULL COMMENT '祖先节点ID',
    `descendant_id` BIGINT NOT NULL COMMENT '后代节点ID',
    `depth` INT NOT NULL DEFAULT 0 COMMENT '层级深度(0表示自己到自己)',
    `customer_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户ID(0表示系统级别)',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_closure_ancestor_descendant` (`ancestor_id`, `descendant_id`, `customer_id`),
    KEY `idx_closure_ancestor` (`ancestor_id`, `customer_id`),
    KEY `idx_closure_descendant` (`descendant_id`, `customer_id`),
    KEY `idx_closure_depth` (`depth`),
    KEY `idx_closure_customer` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织架构闭包关系表';

-- 2. 组织管理员关系缓存表 (性能优化)
CREATE TABLE IF NOT EXISTS `sys_org_manager_cache` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `org_id` BIGINT NOT NULL COMMENT '组织ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `user_name` VARCHAR(50) NOT NULL COMMENT '用户名',
    `role_type` VARCHAR(20) NOT NULL COMMENT '角色类型(manager:管理员,supervisor:主管)',
    `org_level` INT NOT NULL DEFAULT 0 COMMENT '组织层级',
    `customer_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户ID',
    `is_active` TINYINT DEFAULT 1 COMMENT '是否有效(1有效0无效)',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_manager_org_user_role` (`org_id`, `user_id`, `role_type`, `customer_id`),
    KEY `idx_manager_org` (`org_id`, `customer_id`),
    KEY `idx_manager_user` (`user_id`, `customer_id`),
    KEY `idx_manager_role` (`role_type`, `customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织管理员关系缓存表';

-- 3. 从现有sys_org_units表迁移数据到闭包表的存储过程
DELIMITER $$

CREATE PROCEDURE `MigrateToClosureTable`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_org_id BIGINT;
    DECLARE v_parent_id BIGINT;
    DECLARE v_ancestors TEXT;
    DECLARE v_customer_id BIGINT;
    DECLARE ancestor_id BIGINT;
    DECLARE depth_level INT;
    
    -- 游标声明
    DECLARE org_cursor CURSOR FOR 
        SELECT id, parent_id, ancestors, customer_id 
        FROM sys_org_units 
        WHERE is_deleted = 0 
        ORDER BY level, id;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- 清空闭包表
    TRUNCATE TABLE sys_org_closure;
    
    START TRANSACTION;
    
    OPEN org_cursor;
    
    org_loop: LOOP
        FETCH org_cursor INTO v_org_id, v_parent_id, v_ancestors, v_customer_id;
        
        IF done THEN
            LEAVE org_loop;
        END IF;
        
        -- 1. 插入自身到自身的关系 (depth=0)
        INSERT IGNORE INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
        VALUES (v_org_id, v_org_id, 0, v_customer_id);
        
        -- 2. 处理祖先关系
        IF v_ancestors IS NOT NULL AND v_ancestors != '' AND v_ancestors != '0' THEN
            -- 解析ancestors字段 (格式如: 0,1,2,3)
            SET @ancestors_str = CONCAT(v_ancestors, ',');
            SET @pos = 1;
            SET depth_level = 1;
            
            WHILE @pos > 0 DO
                SET @comma_pos = LOCATE(',', @ancestors_str, @pos);
                IF @comma_pos > 0 THEN
                    SET @ancestor_str = SUBSTRING(@ancestors_str, @pos, @comma_pos - @pos);
                    SET ancestor_id = CAST(@ancestor_str AS UNSIGNED);
                    
                    -- 跳过0和自身
                    IF ancestor_id > 0 AND ancestor_id != v_org_id THEN
                        INSERT IGNORE INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
                        VALUES (ancestor_id, v_org_id, depth_level, v_customer_id);
                        SET depth_level = depth_level + 1;
                    END IF;
                    
                    SET @pos = @comma_pos + 1;
                ELSE
                    SET @pos = 0;
                END IF;
            END WHILE;
        END IF;
        
    END LOOP;
    
    CLOSE org_cursor;
    COMMIT;
    
    -- 输出统计信息
    SELECT 
        COUNT(*) as total_closure_records,
        COUNT(DISTINCT ancestor_id) as unique_ancestors,
        COUNT(DISTINCT descendant_id) as unique_descendants,
        MAX(depth) as max_depth
    FROM sys_org_closure;
    
END$$

DELIMITER ;

-- 4. 刷新管理员缓存的存储过程
DELIMITER $$

CREATE PROCEDURE `RefreshOrgManagerCache`()
BEGIN
    START TRANSACTION;
    
    -- 清空缓存表
    TRUNCATE TABLE sys_org_manager_cache;
    
    -- 插入管理员数据
    INSERT INTO sys_org_manager_cache (org_id, user_id, user_name, role_type, org_level, customer_id, is_active)
    SELECT 
        uo.org_id,
        uo.user_id,
        u.user_name,
        'manager' as role_type,
        COALESCE(org.level, 0) as org_level,
        COALESCE(org.customer_id, 0) as customer_id,
        CASE 
            WHEN u.status = '0' AND uo.is_deleted = 0 AND org.status = '0' THEN 1
            ELSE 0
        END as is_active
    FROM sys_user_org uo
    INNER JOIN sys_user u ON uo.user_id = u.id
    INNER JOIN sys_org_units org ON uo.org_id = org.id
    WHERE uo.is_deleted = 0 
      AND u.is_deleted = 0 
      AND org.is_deleted = 0
      AND uo.principal = '1';
    
    COMMIT;
    
    -- 输出统计信息
    SELECT 
        COUNT(*) as total_managers,
        COUNT(CASE WHEN role_type = 'manager' THEN 1 END) as managers,
        COUNT(CASE WHEN role_type = 'supervisor' THEN 1 END) as supervisors,
        COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_managers
    FROM sys_org_manager_cache;
    
END$$

DELIMITER ;

-- 5. 组织数据一致性检查和修复
DELIMITER $$

CREATE PROCEDURE `ValidateClosureTableConsistency`()
BEGIN
    DECLARE inconsistency_count INT DEFAULT 0;
    
    -- 检查1: 每个组织是否都有自身到自身的关系
    SELECT COUNT(*) INTO inconsistency_count
    FROM sys_org_units org
    LEFT JOIN sys_org_closure c ON org.id = c.ancestor_id AND org.id = c.descendant_id AND c.depth = 0
    WHERE org.is_deleted = 0 AND c.id IS NULL;
    
    IF inconsistency_count > 0 THEN
        SELECT CONCAT('发现 ', inconsistency_count, ' 个组织缺少自身关系') as warning_message;
        
        -- 自动修复
        INSERT IGNORE INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
        SELECT org.id, org.id, 0, org.customer_id
        FROM sys_org_units org
        LEFT JOIN sys_org_closure c ON org.id = c.ancestor_id AND org.id = c.descendant_id AND c.depth = 0
        WHERE org.is_deleted = 0 AND c.id IS NULL;
    END IF;
    
    -- 检查2: 闭包表中是否有已删除的组织
    SELECT COUNT(*) INTO inconsistency_count
    FROM sys_org_closure c
    LEFT JOIN sys_org_units org1 ON c.ancestor_id = org1.id
    LEFT JOIN sys_org_units org2 ON c.descendant_id = org2.id
    WHERE (org1.is_deleted = 1 OR org1.id IS NULL) 
       OR (org2.is_deleted = 1 OR org2.id IS NULL);
    
    IF inconsistency_count > 0 THEN
        SELECT CONCAT('发现 ', inconsistency_count, ' 条闭包关系涉及已删除组织') as warning_message;
        
        -- 自动清理
        DELETE c FROM sys_org_closure c
        LEFT JOIN sys_org_units org1 ON c.ancestor_id = org1.id
        LEFT JOIN sys_org_units org2 ON c.descendant_id = org2.id
        WHERE (org1.is_deleted = 1 OR org1.id IS NULL) 
           OR (org2.is_deleted = 1 OR org2.id IS NULL);
    END IF;
    
    SELECT 'Closure table consistency check completed' as result_message;
    
END$$

DELIMITER ;

-- 6. 创建高性能查询视图
CREATE OR REPLACE VIEW `v_org_hierarchy_info` AS
SELECT 
    org.id as org_id,
    org.name as org_name,
    org.code as org_code,
    org.level as org_level,
    org.customer_id,
    -- 直接子部门数量
    (SELECT COUNT(*) 
     FROM sys_org_closure c2 
     INNER JOIN sys_org_units child ON c2.descendant_id = child.id
     WHERE c2.ancestor_id = org.id 
       AND c2.depth = 1 
       AND child.is_deleted = 0
    ) as direct_children_count,
    -- 所有子部门数量
    (SELECT COUNT(*) 
     FROM sys_org_closure c3 
     INNER JOIN sys_org_units child ON c3.descendant_id = child.id
     WHERE c3.ancestor_id = org.id 
       AND c3.depth > 0 
       AND child.is_deleted = 0
    ) as total_children_count,
    -- 管理员数量
    (SELECT COUNT(*) 
     FROM sys_org_manager_cache mc 
     WHERE mc.org_id = org.id 
       AND mc.role_type = 'manager' 
       AND mc.is_active = 1
    ) as manager_count,
    -- 主管数量
    (SELECT COUNT(*) 
     FROM sys_org_manager_cache mc 
     WHERE mc.org_id = org.id 
       AND mc.role_type = 'supervisor' 
       AND mc.is_active = 1
    ) as supervisor_count
FROM sys_org_units org
WHERE org.is_deleted = 0;

-- 7. 创建索引优化查询性能
-- 已在表创建时定义，无需重复创建

-- 执行完成标记
SELECT 'Closure table schema created successfully!' as result_message;