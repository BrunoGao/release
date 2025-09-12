/*
 * Migration: Initialize User Types and Admin Levels
 * Description: Initialize user_type and admin_level fields for all existing users
 * Author: bruno.gao <gaojunivas@gmail.com>
 * Date: 2025-09-12
 * Version: v2.0.2
 *
 * Purpose:
 * - Initialize user_type and admin_level fields based on existing role assignments
 * - Ensure data consistency for the admin user query optimization
 * - Support different admin levels: dept_admin, tenant_admin, super_admin
 */

-- Create temporary stored procedure for user type initialization
DELIMITER $$

CREATE PROCEDURE InitializeUserTypes()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_user_id BIGINT;
    DECLARE v_user_name VARCHAR(64);
    DECLARE v_has_admin_role INT DEFAULT 0;
    DECLARE v_is_top_level_org INT DEFAULT 0;
    DECLARE v_calculated_user_type TINYINT DEFAULT 0;
    DECLARE v_calculated_admin_level TINYINT DEFAULT 0;
    
    -- Cursor to iterate through all users
    DECLARE user_cursor CURSOR FOR 
        SELECT id, user_name FROM sys_user WHERE deleted = 0;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Create temporary table to store user type calculations
    CREATE TEMPORARY TABLE IF NOT EXISTS temp_user_types (
        user_id BIGINT PRIMARY KEY,
        user_type TINYINT DEFAULT 0,
        admin_level TINYINT DEFAULT 0
    );

    OPEN user_cursor;

    user_loop: LOOP
        FETCH user_cursor INTO v_user_id, v_user_name;
        IF done THEN
            LEAVE user_loop;
        END IF;

        -- Initialize variables for each user
        SET v_has_admin_role = 0;
        SET v_is_top_level_org = 0;
        SET v_calculated_user_type = 0; -- Default: NORMAL
        SET v_calculated_admin_level = 0; -- Default: NONE

        -- Check if user is super admin (admin user)
        IF LOWER(v_user_name) = 'admin' THEN
            SET v_calculated_user_type = 3; -- SUPER_ADMIN
            SET v_calculated_admin_level = 3; -- SYSTEM_LEVEL
        ELSE
            -- Check if user has admin roles (is_admin = 1)
            SELECT COUNT(*) INTO v_has_admin_role
            FROM sys_user_role sur
            JOIN sys_role sr ON sur.role_id = sr.id
            WHERE sur.user_id = v_user_id 
                AND sur.deleted = 0 
                AND sr.deleted = 0
                AND sr.is_admin = 1;

            IF v_has_admin_role > 0 THEN
                -- Check if user is in top-level organization (tenant level)
                SELECT COUNT(*) INTO v_is_top_level_org
                FROM sys_user_org suo
                JOIN sys_org_units sou ON suo.org_id = sou.id
                WHERE suo.user_id = v_user_id 
                    AND suo.deleted = 0 
                    AND sou.deleted = 0
                    AND (sou.parent_id IS NULL OR sou.parent_id = 0 OR sou.parent_id = 1);

                IF v_is_top_level_org > 0 THEN
                    SET v_calculated_user_type = 2; -- TENANT_ADMIN
                    SET v_calculated_admin_level = 2; -- TENANT_LEVEL
                ELSE
                    SET v_calculated_user_type = 1; -- DEPT_ADMIN
                    SET v_calculated_admin_level = 1; -- DEPT_LEVEL
                END IF;
            END IF;
        END IF;

        -- Store the calculated values
        INSERT INTO temp_user_types (user_id, user_type, admin_level) 
        VALUES (v_user_id, v_calculated_user_type, v_calculated_admin_level)
        ON DUPLICATE KEY UPDATE 
            user_type = v_calculated_user_type,
            admin_level = v_calculated_admin_level;

    END LOOP;

    CLOSE user_cursor;

    -- Apply the calculated values to sys_user table
    UPDATE sys_user su
    JOIN temp_user_types tut ON su.id = tut.user_id
    SET su.user_type = tut.user_type,
        su.admin_level = tut.admin_level,
        su.update_time = NOW()
    WHERE su.deleted = 0;

    -- Get statistics
    SELECT 
        COUNT(*) as total_users,
        SUM(CASE WHEN user_type = 0 THEN 1 ELSE 0 END) as normal_users,
        SUM(CASE WHEN user_type = 1 THEN 1 ELSE 0 END) as dept_admins,
        SUM(CASE WHEN user_type = 2 THEN 1 ELSE 0 END) as tenant_admins,
        SUM(CASE WHEN user_type = 3 THEN 1 ELSE 0 END) as super_admins
    FROM temp_user_types;

    -- Clean up
    DROP TEMPORARY TABLE temp_user_types;

END$$

DELIMITER ;

-- Execute the initialization procedure
CALL InitializeUserTypes();

-- Drop the procedure after execution
DROP PROCEDURE InitializeUserTypes;

-- Verify the results
SELECT 
    user_type,
    admin_level,
    COUNT(*) as user_count,
    CASE user_type
        WHEN 0 THEN 'NORMAL'
        WHEN 1 THEN 'DEPT_ADMIN'
        WHEN 2 THEN 'TENANT_ADMIN'
        WHEN 3 THEN 'SUPER_ADMIN'
        ELSE 'UNKNOWN'
    END as user_type_name,
    CASE admin_level
        WHEN 0 THEN 'NONE'
        WHEN 1 THEN 'DEPT_LEVEL'
        WHEN 2 THEN 'TENANT_LEVEL'
        WHEN 3 THEN 'SYSTEM_LEVEL'
        ELSE 'UNKNOWN'
    END as admin_level_name
FROM sys_user 
WHERE deleted = 0
GROUP BY user_type, admin_level
ORDER BY user_type, admin_level;

-- Create indexes if they don't exist (from previous migration)
CREATE INDEX IF NOT EXISTS idx_user_type ON sys_user(user_type);
CREATE INDEX IF NOT EXISTS idx_admin_level ON sys_user(admin_level);
CREATE INDEX IF NOT EXISTS idx_user_org_admin ON sys_user(org_id, admin_level);
CREATE INDEX IF NOT EXISTS idx_user_customer_admin ON sys_user(customer_id, admin_level);

-- Log migration completion
INSERT INTO migration_log (version, description, executed_at, status) 
VALUES ('009', 'Initialize user types and admin levels for existing users', NOW(), 'SUCCESS')
ON DUPLICATE KEY UPDATE 
    executed_at = NOW(), 
    status = 'SUCCESS';

SELECT '✅ Migration 009: User types initialization completed successfully' as status;