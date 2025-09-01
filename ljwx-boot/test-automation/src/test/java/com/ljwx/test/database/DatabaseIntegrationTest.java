package com.ljwx.test.database;

import lombok.extern.slf4j.Slf4j;
import org.testcontainers.containers.MySQLContainer;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * 数据库集成测试
 * 验证数据库性能优化效果和数据完整性
 */
@Slf4j
public class DatabaseIntegrationTest {
    
    private MySQLContainer<?> mysql;
    private Connection connection;
    
    @BeforeClass
    public void setup() throws SQLException {
        // 启动MySQL容器
        mysql = new MySQLContainer<>("mysql:8.0")
                .withDatabaseName("ljwx_test")
                .withUsername("test")
                .withPassword("test")
                .withCommand("--character-set-server=utf8mb4", 
                           "--collation-server=utf8mb4_0900_ai_ci");
        
        mysql.start();
        
        // 建立数据库连接
        connection = DriverManager.getConnection(
            mysql.getJdbcUrl(),
            mysql.getUsername(), 
            mysql.getPassword()
        );
        
        // 初始化测试数据
        initializeTestData();
        
        log.info("数据库集成测试环境初始化完成");
    }
    
    @AfterClass
    public void cleanup() throws SQLException {
        if (connection != null) {
            connection.close();
        }
        if (mysql != null) {
            mysql.stop();
        }
    }
    
    /**
     * 初始化测试数据
     */
    private void initializeTestData() throws SQLException {
        // 创建组织表结构
        executeSQL("""
            CREATE TABLE sys_org_units (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                parent_id BIGINT,
                level INT DEFAULT 1,
                is_deleted TINYINT(1) DEFAULT 0,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """);
        
        // 创建闭包表
        executeSQL("""
            CREATE TABLE sys_org_closure (
                ancestor BIGINT NOT NULL,
                descendant BIGINT NOT NULL,
                depth INT NOT NULL DEFAULT 0,
                PRIMARY KEY (ancestor, descendant),
                KEY idx_descendant (descendant),
                KEY idx_depth (depth)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """);
        
        // 插入测试组织数据
        insertTestOrganizations();
        
        log.info("测试数据初始化完成");
    }
    
    /**
     * 插入测试组织数据
     */
    private void insertTestOrganizations() throws SQLException {
        // 插入根组织
        executeSQL("INSERT INTO sys_org_units (id, name, parent_id, level) VALUES (1, '总公司', NULL, 1)");
        executeSQL("INSERT INTO sys_org_closure (ancestor, descendant, depth) VALUES (1, 1, 0)");
        
        // 插入子组织（深度3层，每层5个组织）
        for (int level = 2; level <= 4; level++) {
            for (int i = 1; i <= 5; i++) {
                long orgId = (level - 1) * 5 + i;
                long parentId = level == 2 ? 1 : ((level - 2) * 5 + 1);
                String orgName = String.format("部门%d-%d", level - 1, i);
                
                // 插入组织
                executeSQL(String.format(
                    "INSERT INTO sys_org_units (id, name, parent_id, level) VALUES (%d, '%s', %d, %d)",
                    orgId, orgName, parentId, level
                ));
                
                // 插入闭包关系
                executeSQL(String.format(
                    "INSERT INTO sys_org_closure (ancestor, descendant, depth) VALUES (%d, %d, 0)",
                    orgId, orgId
                ));
                
                // 插入与所有祖先的关系
                try (PreparedStatement stmt = connection.prepareStatement(
                    "INSERT INTO sys_org_closure (ancestor, descendant, depth) " +
                    "SELECT ancestor, ?, depth + 1 FROM sys_org_closure WHERE descendant = ?"
                )) {
                    stmt.setLong(1, orgId);
                    stmt.setLong(2, parentId);
                    stmt.executeUpdate();
                }
            }
        }
        
        log.info("插入了 {} 个测试组织", 1 + 5 * 3);
    }
    
    @Test(priority = 1, description = "验证闭包表查询性能")
    public void testClosureTableQueryPerformance() throws SQLException {
        log.info("开始验证闭包表查询性能...");
        
        long startTime = System.currentTimeMillis();
        
        // 查询所有子组织（使用闭包表）
        List<Long> childOrgIds = new ArrayList<>();
        try (PreparedStatement stmt = connection.prepareStatement("""
            SELECT o.id, o.name, c.depth 
            FROM sys_org_units o
            JOIN sys_org_closure c ON o.id = c.descendant 
            WHERE c.ancestor = 1 AND o.is_deleted = 0
            ORDER BY c.depth, o.id
        """)) {
            
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    childOrgIds.add(rs.getLong("id"));
                }
            }
        }
        
        long endTime = System.currentTimeMillis();
        long queryTime = endTime - startTime;
        
        log.info("闭包表查询耗时: {}ms, 查询到 {} 个组织", queryTime, childOrgIds.size());
        
        // 验证查询结果
        Assert.assertTrue(childOrgIds.size() >= 15, "应该查询到至少15个组织");
        Assert.assertTrue(queryTime < 100, "闭包表查询应该在100ms内完成，实际: " + queryTime + "ms");
        
        log.info("✅ 闭包表查询性能验证通过");
    }
    
    @Test(priority = 2, description = "验证传统递归查询性能对比")
    public void testTraditionalRecursiveQueryPerformance() throws SQLException {
        log.info("开始验证传统递归查询性能...");
        
        long startTime = System.currentTimeMillis();
        
        // 模拟传统递归查询（性能较差的方式）
        List<Long> childOrgIds = getChildOrganizationsRecursive(1L);
        
        long endTime = System.currentTimeMillis();
        long queryTime = endTime - startTime;
        
        log.info("递归查询耗时: {}ms, 查询到 {} 个组织", queryTime, childOrgIds.size());
        
        // 验证查询结果
        Assert.assertTrue(childOrgIds.size() >= 15, "递归查询应该查询到至少15个组织");
        
        log.info("📊 传统递归查询性能基准: {}ms", queryTime);
    }
    
    @Test(priority = 3, description = "验证数据完整性约束")
    public void testDataIntegrityConstraints() throws SQLException {
        log.info("开始验证数据完整性约束...");
        
        // 验证闭包表数据完整性
        try (PreparedStatement stmt = connection.prepareStatement("""
            SELECT COUNT(*) as closure_count FROM sys_org_closure
        """)) {
            try (ResultSet rs = stmt.executeQuery()) {
                rs.next();
                int closureCount = rs.getInt("closure_count");
                Assert.assertTrue(closureCount > 15, "闭包表应该有足够的关系记录");
                log.info("闭包表关系记录数: {}", closureCount);
            }
        }
        
        // 验证组织层级完整性
        try (PreparedStatement stmt = connection.prepareStatement("""
            SELECT o.id, o.name, COUNT(c.ancestor) as ancestor_count
            FROM sys_org_units o
            LEFT JOIN sys_org_closure c ON o.id = c.descendant AND c.ancestor != c.descendant
            WHERE o.is_deleted = 0
            GROUP BY o.id, o.name
            HAVING ancestor_count = 0 AND o.parent_id IS NOT NULL
        """)) {
            try (ResultSet rs = stmt.executeQuery()) {
                Assert.assertFalse(rs.next(), "不应该存在缺失祖先关系的组织");
            }
        }
        
        log.info("✅ 数据完整性约束验证通过");
    }
    
    @Test(priority = 4, description = "验证字符集和排序规则")
    public void testCharsetAndCollation() throws SQLException {
        log.info("开始验证字符集和排序规则...");
        
        // 验证表字符集
        try (PreparedStatement stmt = connection.prepareStatement("""
            SELECT TABLE_NAME, TABLE_COLLATION 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME IN ('sys_org_units', 'sys_org_closure')
        """)) {
            stmt.setString(1, "ljwx_test");
            
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    String tableName = rs.getString("TABLE_NAME");
                    String collation = rs.getString("TABLE_COLLATION");
                    
                    Assert.assertEquals(collation, "utf8mb4_0900_ai_ci", 
                        "表 " + tableName + " 字符集应该为 utf8mb4_0900_ai_ci");
                }
            }
        }
        
        log.info("✅ 字符集和排序规则验证通过");
    }
    
    /**
     * 传统递归查询子组织（性能较差的方法）
     */
    private List<Long> getChildOrganizationsRecursive(Long parentId) throws SQLException {
        List<Long> result = new ArrayList<>();
        result.add(parentId);
        
        try (PreparedStatement stmt = connection.prepareStatement(
            "SELECT id FROM sys_org_units WHERE parent_id = ? AND is_deleted = 0"
        )) {
            stmt.setLong(1, parentId);
            
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Long childId = rs.getLong("id");
                    result.addAll(getChildOrganizationsRecursive(childId));
                }
            }
        }
        
        return result;
    }
    
    /**
     * 执行SQL语句
     */
    private void executeSQL(String sql) throws SQLException {
        try (Statement stmt = connection.createStatement()) {
            stmt.execute(sql);
        }
    }
}