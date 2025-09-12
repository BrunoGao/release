# 管理员用户查询优化方案

## 📋 当前问题分析

### 1. ljwx-boot 当前实现分析

#### 当前的管理员判断逻辑
```java
// 1. isAdminUser() - 需要查询 sys_user_role + sys_role 两张表
public boolean isAdminUser(Long userId) {
    return sysUserRoleService.list(new LambdaQueryWrapper<SysUserRole>()
        .eq(SysUserRole::getUserId, userId)
        .eq(SysUserRole::getDeleted, false))
        .stream()
        .anyMatch(userRole -> {
            SysRole role = sysRoleService.getById(userRole.getRoleId());  // 又一次数据库查询
            return role != null && role.getIsAdmin() != null && role.getIsAdmin() == 1;
        });
}

// 2. isSuperAdmin() - 查询 sys_user 表，检查用户名
public boolean isSuperAdmin(Long userId) {
    SysUser user = baseMapper.selectById(userId);
    return StringPools.ADMIN.equalsIgnoreCase(user.getUserName());
}

// 3. isTopLevelDeptAdmin() - 需要查询 sys_user_org + sys_org_units 表
public boolean isTopLevelDeptAdmin(Long userId) {
    if (!isAdminUser(userId)) return false;  // 又调用了 isAdminUser()
    
    List<SysUserOrg> userOrgs = sysUserOrgService.list(...);
    return userOrgs.stream().anyMatch(userOrg -> {
        SysOrgUnits org = sysOrgUnitsService.getById(userOrg.getOrgId());  // 又一次数据库查询
        return org != null && isTopLevelOrg(org.getParentId());
    });
}
```

#### 当前使用场景统计
通过代码分析，发现以下高频使用场景：

**ljwx-boot 中的调用点：**
- `TWechatAlertConfigController` - 权限控制 (2处)
- `SysOrgUnitsController` - 租户创建权限 (1处)
- `SysPositionController` - 职位管理权限 (2处)
- `TUserHealthDataServiceImpl` - 健康数据过滤 (1处)
- `OrgStatisticsServiceImpl` - 统计时排除管理员 (1处)
- `SysPositionFacadeImpl` - 职位查询权限 (4处)
- `SysUserFacadeImpl` - 用户列表权限 (1处)
- `SysUserServiceImpl` - 用户查询时过滤 (1处)

**ljwx-bigscreen 中的使用：**
- 目前主要通过 ljwx-boot API 调用，没有直接的用户类型判断逻辑

### 2. 性能问题分析

#### 当前查询复杂度
1. **isAdminUser()**: 
   - 1次 sys_user_role 表查询
   - N次 sys_role 表查询 (N=用户角色数量)
   - 总查询: 1 + N 次

2. **isTopLevelDeptAdmin()**:
   - 调用 isAdminUser() → 1 + N 次查询
   - 1次 sys_user_org 表查询  
   - M次 sys_org_units 表查询 (M=用户组织数量)
   - 总查询: 2 + N + M 次

3. **批量用户类型判断**:
   - 如果需要判断100个用户，可能产生 200+ 次数据库查询

#### 高频场景的性能影响
```java
// 例如：组织统计时过滤管理员用户
.filter(user -> !sysUserService.isAdminUser(user.getId()))

// 如果组织有50个用户，每个用户平均2个角色，则产生：
// 50 * (1 + 2) = 150次数据库查询
```

## 🎯 优化方案设计

### 方案一：添加用户类型冗余字段 (推荐)

#### 1. 数据库表结构扩展

```sql
-- 在 sys_user 表中添加用户类型字段
ALTER TABLE sys_user ADD COLUMN user_type TINYINT DEFAULT 0 COMMENT '用户类型: 0=普通用户, 1=部门管理员, 2=租户管理员, 3=超级管理员';
ALTER TABLE sys_user ADD COLUMN admin_level TINYINT DEFAULT 0 COMMENT '管理级别: 0=非管理员, 1=部门级, 2=租户级, 3=系统级';
ALTER TABLE sys_user ADD INDEX idx_user_type (user_type);
ALTER TABLE sys_user ADD INDEX idx_admin_level (admin_level);
ALTER TABLE sys_user ADD INDEX idx_org_admin (org_id, admin_level); -- 组织管理员复合索引
ALTER TABLE sys_user ADD INDEX idx_customer_admin (customer_id, admin_level); -- 租户管理员复合索引
```

#### 2. 用户类型枚举定义

```java
public enum UserType {
    NORMAL(0, "普通用户"),
    DEPT_ADMIN(1, "部门管理员"), 
    TENANT_ADMIN(2, "租户管理员"),
    SUPER_ADMIN(3, "超级管理员");
    
    private final int code;
    private final String desc;
}

public enum AdminLevel {
    NONE(0, "非管理员"),
    DEPT_LEVEL(1, "部门级管理员"),
    TENANT_LEVEL(2, "租户级管理员"), 
    SYSTEM_LEVEL(3, "系统级管理员");
    
    private final int code;
    private final String desc;
}
```

#### 3. 优化后的查询方法

```java
// 替换原有的复杂查询逻辑
public boolean isAdminUser(Long userId) {
    SysUser user = this.getById(userId);
    return user != null && user.getAdminLevel() > 0;
}

public boolean isSuperAdmin(Long userId) {
    SysUser user = this.getById(userId);
    return user != null && user.getUserType() == UserType.SUPER_ADMIN.getCode();
}

public boolean isTopLevelDeptAdmin(Long userId) {
    SysUser user = this.getById(userId);
    return user != null && (user.getUserType() == UserType.TENANT_ADMIN.getCode() || 
                           user.getUserType() == UserType.SUPER_ADMIN.getCode());
}

// 批量查询优化
public Map<Long, UserType> batchGetUserTypes(List<Long> userIds) {
    return this.listByIds(userIds).stream()
        .collect(Collectors.toMap(SysUser::getId, 
            user -> UserType.fromCode(user.getUserType())));
}

// 高效的组织管理员查询
public List<SysUser> getOrgAdmins(Long orgId) {
    return this.list(new LambdaQueryWrapper<SysUser>()
        .eq(SysUser::getOrgId, orgId)
        .gt(SysUser::getAdminLevel, 0)); // 直接查询管理员
}

// 高效的租户管理员查询  
public List<SysUser> getTenantAdmins(Long customerId) {
    return this.list(new LambdaQueryWrapper<SysUser>()
        .eq(SysUser::getCustomerId, customerId)
        .ge(SysUser::getAdminLevel, AdminLevel.TENANT_LEVEL.getCode()));
}
```

#### 4. 数据同步和维护机制

```java
// 用户角色变更时同步更新用户类型
@Override
@Transactional
public boolean updateUserRole(Long userId, List<Long> roleIds) {
    // 原有角色更新逻辑
    boolean roleUpdated = super.updateUserRole(userId, roleIds);
    
    // 同步更新用户类型
    if (roleUpdated) {
        updateUserTypeFromRoles(userId, roleIds);
    }
    
    return roleUpdated;
}

private void updateUserTypeFromRoles(Long userId, List<Long> roleIds) {
    // 查询角色的管理员属性
    List<SysRole> roles = sysRoleService.listByIds(roleIds);
    
    UserType userType = calculateUserType(roles);
    AdminLevel adminLevel = calculateAdminLevel(roles);
    
    // 更新用户类型字段
    SysUser updateUser = new SysUser();
    updateUser.setId(userId);
    updateUser.setUserType(userType.getCode());
    updateUser.setAdminLevel(adminLevel.getCode());
    
    this.updateById(updateUser);
}

// 组织变更时同步更新用户类型
@Override  
public boolean updateUserOrg(Long userId, List<Long> orgIds, List<Long> principalIds) {
    boolean orgUpdated = super.updateUserOrg(userId, orgIds, principalIds);
    
    if (orgUpdated) {
        // 重新计算用户管理级别（可能从部门管理员变为租户管理员）
        recalculateUserAdminLevel(userId);
    }
    
    return orgUpdated;
}
```

### 方案二：智能缓存优化 (辅助方案)

#### 1. Redis 缓存方案
```java
@Service
public class UserTypeCache {
    
    private static final String CACHE_PREFIX = "user_type:";
    private static final int CACHE_TTL = 3600; // 1小时
    
    public UserType getUserType(Long userId) {
        String cacheKey = CACHE_PREFIX + userId;
        String cached = redisTemplate.opsForValue().get(cacheKey);
        
        if (cached != null) {
            return UserType.fromCode(Integer.parseInt(cached));
        }
        
        // 缓存未命中，查询数据库
        UserType userType = calculateUserTypeFromDB(userId);
        redisTemplate.opsForValue().set(cacheKey, String.valueOf(userType.getCode()), CACHE_TTL);
        
        return userType;
    }
    
    // 批量缓存查询
    public Map<Long, UserType> batchGetUserTypes(List<Long> userIds) {
        List<String> cacheKeys = userIds.stream()
            .map(id -> CACHE_PREFIX + id)
            .collect(Collectors.toList());
            
        List<String> cachedValues = redisTemplate.opsForValue().multiGet(cacheKeys);
        
        Map<Long, UserType> result = new HashMap<>();
        List<Long> missedIds = new ArrayList<>();
        
        for (int i = 0; i < userIds.size(); i++) {
            if (cachedValues.get(i) != null) {
                result.put(userIds.get(i), UserType.fromCode(Integer.parseInt(cachedValues.get(i))));
            } else {
                missedIds.add(userIds.get(i));
            }
        }
        
        // 批量查询未命中的数据
        if (!missedIds.isEmpty()) {
            Map<Long, UserType> dbResult = calculateUserTypesFromDB(missedIds);
            result.putAll(dbResult);
            
            // 批量更新缓存
            Map<String, String> cacheData = dbResult.entrySet().stream()
                .collect(Collectors.toMap(
                    entry -> CACHE_PREFIX + entry.getKey(),
                    entry -> String.valueOf(entry.getValue().getCode())
                ));
            redisTemplate.opsForValue().multiSet(cacheData);
        }
        
        return result;
    }
    
    // 缓存失效
    public void invalidateUserCache(Long userId) {
        redisTemplate.delete(CACHE_PREFIX + userId);
    }
}
```

## 📊 性能对比分析

### 查询复杂度对比

| 场景 | 当前方案 | 优化方案一 | 优化方案二 |
|------|----------|------------|------------|
| 单用户类型查询 | 1+N次DB查询 | 1次DB查询 | 1次Redis查询 |
| 批量用户类型查询(100用户) | 200+次DB查询 | 1次DB查询 | 1次Redis查询 |
| 组织管理员查询 | N*(1+M)次DB查询 | 1次DB查询 | 1次Redis查询 |
| 租户管理员查询 | N*(2+M)次DB查询 | 1次DB查询 | 1次Redis查询 |

### 预估性能提升

#### 高频场景优化效果：
1. **组织统计场景**（50用户过滤）
   - 当前：150次数据库查询
   - 优化后：1次数据库查询
   - **性能提升：99.3%**

2. **权限控制场景**（单用户判断）
   - 当前：平均3次数据库查询
   - 优化后：1次数据库查询 或 Redis缓存
   - **性能提升：66.7%**

3. **批量用户类型判断**（100用户）
   - 当前：200+次数据库查询
   - 优化后：1次数据库查询
   - **性能提升：99.5%**

## 🚀 实施建议

### 阶段一：字段扩展和索引优化
1. 添加 `user_type` 和 `admin_level` 字段
2. 创建相关索引
3. 编写数据同步脚本，初始化现有用户的类型字段

### 阶段二：查询方法重构
1. 重构 `isAdminUser`, `isSuperAdmin`, `isTopLevelDeptAdmin` 等方法
2. 添加批量查询方法
3. 添加高效的组织/租户管理员查询方法

### 阶段三：数据同步机制
1. 在角色变更时同步更新用户类型
2. 在组织关系变更时重新计算管理级别
3. 添加数据一致性检查工具

### 阶段四：缓存机制（可选）
1. 实施 Redis 缓存
2. 添加缓存失效机制
3. 监控缓存命中率

## 🔧 迁移策略

### 1. 数据初始化脚本
```sql
-- 初始化用户类型字段
UPDATE sys_user su 
SET user_type = CASE 
    WHEN su.user_name = 'admin' THEN 3  -- 超级管理员
    WHEN EXISTS (
        SELECT 1 FROM sys_user_role sur 
        JOIN sys_role sr ON sur.role_id = sr.id 
        WHERE sur.user_id = su.id AND sr.is_admin = 1 AND sr.deleted = 0
    ) THEN CASE
        WHEN EXISTS (
            SELECT 1 FROM sys_user_org suo
            JOIN sys_org_units sou ON suo.org_id = sou.id
            WHERE suo.user_id = su.id AND (sou.parent_id IS NULL OR sou.parent_id IN (0, 1))
        ) THEN 2  -- 租户管理员
        ELSE 1    -- 部门管理员
    END
    ELSE 0        -- 普通用户
END,
admin_level = CASE 
    WHEN su.user_name = 'admin' THEN 3
    WHEN user_type > 0 THEN user_type
    ELSE 0
END;
```

### 2. 渐进式部署
1. **向后兼容**：保留原有方法，新增优化方法
2. **逐步替换**：按模块逐步替换调用
3. **性能监控**：监控查询性能变化
4. **回滚预案**：保留原有逻辑作为备选

### 3. 测试验证
```java
@Test
public void testUserTypeConsistency() {
    List<Long> userIds = getUserIds(); // 获取所有用户ID
    
    for (Long userId : userIds) {
        // 对比新旧方法的结果一致性
        boolean oldIsAdmin = oldIsAdminUser(userId);
        boolean newIsAdmin = newIsAdminUser(userId);
        
        assertEquals(oldIsAdmin, newIsAdmin, "用户" + userId + "的管理员判断结果不一致");
    }
}
```

## 📈 监控和维护

### 1. 数据一致性监控
```sql
-- 检查数据一致性的SQL
SELECT 
    u.id,
    u.user_name,
    u.user_type,
    u.admin_level,
    COUNT(CASE WHEN r.is_admin = 1 THEN 1 END) as admin_role_count
FROM sys_user u
LEFT JOIN sys_user_role ur ON u.id = ur.user_id AND ur.deleted = 0
LEFT JOIN sys_role r ON ur.role_id = r.id AND r.deleted = 0
WHERE u.deleted = 0
GROUP BY u.id, u.user_name, u.user_type, u.admin_level
HAVING (u.admin_level > 0 AND admin_role_count = 0) 
    OR (u.admin_level = 0 AND admin_role_count > 0);
```

### 2. 性能监控指标
- 管理员判断查询平均响应时间
- 批量用户类型查询响应时间  
- 数据库连接池使用率
- 缓存命中率（如使用缓存方案）

### 3. 数据同步任务
```java
@Scheduled(cron = "0 0 2 * * ?") // 每日凌晨2点执行
public void syncUserTypeData() {
    log.info("开始同步用户类型数据");
    
    // 检查数据一致性
    List<Long> inconsistentUsers = findInconsistentUsers();
    
    // 修复不一致的数据
    for (Long userId : inconsistentUsers) {
        recalculateUserType(userId);
    }
    
    log.info("用户类型数据同步完成，修复{}个不一致记录", inconsistentUsers.size());
}
```

## 🎯 预期收益

### 1. 性能收益
- **查询响应时间减少90%以上**
- **数据库负载降低80%以上**  
- **并发处理能力提升3-5倍**

### 2. 维护收益
- **代码逻辑简化**，易于理解和维护
- **减少跨表查询**，降低数据一致性风险
- **统一的用户类型管理**，便于扩展新的管理员类型

### 3. 业务收益
- **提升用户体验**，页面加载更快
- **支持更大规模**的用户和组织管理
- **为后续功能扩展**奠定基础

---

**备注**：本方案建议优先实施方案一（冗余字段），如对缓存管理有经验的团队可考虑同时实施方案二以获得更佳性能表现。