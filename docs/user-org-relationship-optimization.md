# 用户组织关系优化方案

## 概述
为了简化用户-组织关系查询，提高系统性能，决定对`sys_user`表结构进行扩充，添加冗余的组织信息字段，并建立相应的数据同步机制。

## 问题分析
### 当前问题
1. `SysUser`实体缺少`orgId`和组织相关字段
2. 查询用户组织信息需要多表关联，性能较差
3. 健康数据处理时无法直接获取用户组织信息
4. 组织相关的统计查询复杂度高

### 影响范围
- 健康基线生成服务
- 组织健康统计功能
- 用户管理相关查询
- 权限验证和数据过滤

## 解决方案

### 1. 数据库表结构扩充

#### 1.1 修改sys_user表
添加以下字段：
- `org_id` BIGINT - 组织ID
- `org_name` VARCHAR(100) - 组织名称（冗余存储，提高查询性能）

```sql
-- 扩充sys_user表结构
ALTER TABLE sys_user 
ADD COLUMN org_id BIGINT COMMENT '组织ID',
ADD COLUMN org_name VARCHAR(100) COMMENT '组织名称';

-- 添加索引提高查询性能
CREATE INDEX idx_sys_user_org_id ON sys_user(org_id);
CREATE INDEX idx_sys_user_org_name ON sys_user(org_name);
```

#### 1.2 创建或确保sys_org表存在
```sql
-- 创建组织表（如果不存在）
CREATE TABLE IF NOT EXISTS sys_org (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    org_name VARCHAR(100) NOT NULL COMMENT '组织名称',
    parent_id BIGINT DEFAULT 0 COMMENT '父级组织ID',
    org_code VARCHAR(50) COMMENT '组织编码',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status TINYINT DEFAULT 1 COMMENT '状态(0:禁用,1:启用)',
    is_deleted TINYINT DEFAULT 0 COMMENT '是否删除(0:否,1:是)',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) COMMENT='组织机构表';

-- 添加索引
CREATE INDEX idx_sys_org_parent_id ON sys_org(parent_id);
CREATE INDEX idx_sys_org_code ON sys_org(org_code);
```

### 2. 实体类修改

#### 2.1 SysUser实体类扩充
```java
/**
 * 组织ID
 */
@TableField("org_id")
private Long orgId;

/**
 * 组织名称（冗余存储）
 */
@TableField("org_name")
private String orgName;

/**
 * 生日（用于年龄计算）
 */
@TableField("birthday")
private LocalDate birthday;
```

#### 2.2 创建SysOrg实体类
```java
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("sys_org")
public class SysOrg extends BaseEntity {
    
    private String orgName;
    private Long parentId;
    private String orgCode;
    private Integer sortOrder;
    private String status;
    private Integer isDeleted;
}
```

### 3. 数据同步机制

#### 3.1 事件驱动同步
使用Spring事件机制在组织信息变更时自动同步用户表：

```java
// 组织变更事件
@Component
public class OrgChangeEventListener {
    
    @EventListener
    @Async
    public void handleOrgNameChange(OrgNameChangeEvent event) {
        // 同步更新所有该组织用户的org_name
        userService.updateOrgNameByOrgId(event.getOrgId(), event.getNewOrgName());
    }
    
    @EventListener  
    @Async
    public void handleOrgDelete(OrgDeleteEvent event) {
        // 清理被删除组织的用户关联
        userService.clearOrgInfoByOrgId(event.getOrgId());
    }
}
```

#### 3.2 用户操作时同步
在用户新增、修改时自动设置组织信息：

```java
@Service
public class SysUserService {
    
    public void saveOrUpdateUser(SysUser user) {
        if (user.getOrgId() != null) {
            // 自动填充组织名称
            SysOrg org = sysOrgService.getById(user.getOrgId());
            if (org != null) {
                user.setOrgName(org.getOrgName());
            }
        }
        // 保存用户
        saveOrUpdate(user);
    }
}
```

### 4. 数据迁移策略

#### 4.1 初始化现有数据
```sql
-- 如果已有用户数据，需要初始化组织信息
-- 假设通过其他表关联获取组织信息，这里需要根据实际情况调整

-- 示例：为现有用户设置默认组织
UPDATE sys_user SET 
    org_id = 1, 
    org_name = '默认组织'
WHERE org_id IS NULL;

-- 示例：从用户设备信息推断组织关系（如果存在相关表）
-- UPDATE sys_user u 
-- JOIN user_device_mapping d ON u.device_sn = d.device_sn
-- JOIN device_org_mapping o ON d.org_id = o.org_id
-- SET u.org_id = o.org_id, u.org_name = o.org_name;
```

#### 4.2 数据一致性检查
```java
@Component
@Slf4j
public class UserOrgConsistencyChecker {
    
    @Scheduled(cron = "0 0 2 * * ?") // 每天凌晨2点执行
    public void checkUserOrgConsistency() {
        // 检查用户表中org_name与org表是否一致
        List<SysUser> inconsistentUsers = userService.findInconsistentOrgUsers();
        
        for (SysUser user : inconsistentUsers) {
            SysOrg org = sysOrgService.getById(user.getOrgId());
            if (org != null && !org.getOrgName().equals(user.getOrgName())) {
                user.setOrgName(org.getOrgName());
                userService.updateById(user);
                log.info("修复用户{}的组织名称不一致问题", user.getUserName());
            }
        }
    }
}
```

## 实施步骤

### 第一阶段：数据库结构调整
1. ✅ 扩充sys_user表结构
2. ✅ 创建sys_org表
3. ✅ 添加相关索引
4. ✅ 初始化现有用户的组织信息

### 第二阶段：代码调整
1. 修改SysUser实体类
2. 创建SysOrg实体类和相关服务
3. 实现数据同步机制
4. 修改健康基线服务使用新字段

### 第三阶段：测试验证
1. 单元测试覆盖
2. 数据一致性验证
3. 性能测试对比
4. 功能回归测试

### 第四阶段：部署上线
1. 生产环境数据备份
2. 数据库结构变更
3. 应用代码部署
4. 数据一致性检查

## 风险评估与应对

### 潜在风险
1. **数据不一致风险**：冗余存储可能导致数据不一致
2. **迁移风险**：现有数据迁移可能出现问题  
3. **性能影响**：表结构变更可能影响现有查询

### 应对措施
1. 建立完善的数据同步机制和一致性检查
2. 充分的测试验证和回滚预案
3. 分阶段灰度发布，监控性能指标

## 预期收益

### 性能提升
- 用户组织查询性能提升80%+
- 减少复杂的多表关联查询
- 健康数据统计查询简化

### 开发效率
- 简化组织相关业务逻辑
- 降低代码复杂度
- 提高开发和维护效率

### 系统稳定性
- 减少数据库查询压力
- 提高系统响应速度
- 降低因复杂查询导致的故障风险

## 监控指标

### 数据质量指标
- 用户组织信息一致性比例
- 数据同步延迟时间
- 数据修复次数

### 性能指标  
- 用户查询响应时间
- 组织统计查询响应时间
- 数据库连接池使用率

### 业务指标
- 健康基线生成成功率
- 组织健康统计准确性
- 用户管理操作效率

---

**实施负责人**: bruno.gao  
**预计完成时间**: 2025-01-27  
**风险等级**: 中等  
**优先级**: 高  