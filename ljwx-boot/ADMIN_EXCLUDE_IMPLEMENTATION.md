# 管理员排除功能实施方案

## 概述
实现系统中员工统计、员工列表不包含管理员角色用户的功能。通过在`sys_role`表增加`is_admin`字段标记管理员角色，在查询时排除相关用户。

## 数据库变更

### 1. 表结构变更
```sql
-- 在sys_role表中增加is_admin字段
ALTER TABLE sys_role 
ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为管理员角色（0普通角色，1管理员角色）' AFTER status;
```

### 2. 数据初始化
```sql
-- 将ADMIN和DAdmin角色标记为管理员角色
UPDATE sys_role SET is_admin = 1 WHERE role_code IN ('ADMIN', 'DAdmin');

-- 确保其他角色为普通角色
UPDATE sys_role SET is_admin = 0 WHERE role_code NOT IN ('ADMIN', 'DAdmin');
```

## 代码实现

### 1. 实体类更新
- **SysRole.java**: 增加`isAdmin`字段
- **SysRoleMapper.xml**: 更新查询结果映射和字段列表

### 2. 服务层实现
- **ISysUserService.java**: 新增`listNonAdminUsersPage`方法
- **SysUserServiceImpl.java**: 实现非管理员用户分页查询
- **SysUserMapper.java**: 新增查询接口
- **SysUserMapper.xml**: 实现排除管理员的SQL查询

### 3. 门面层实现
- **ISysUserFacade.java**: 新增非管理员用户查询接口
- **SysUserFacadeImpl.java**: 实现门面层逻辑

### 4. 控制器层实现
- **EmployeeController.java**: 新增员工管理控制器，专门提供排除管理员的API
- **AuthenticationController.java**: 更新用户信息接口注释

### 5. 统计服务更新
- **OrgStatisticsServiceImpl.java**: 在员工统计中排除管理员用户

## API接口

### 1. 员工分页查询（排除管理员）
```
GET /employee/page
权限：employee:page
描述：分页查询员工列表，自动排除管理员角色用户
```

### 2. 员工列表查询（排除管理员）
```
GET /employee/list  
权限：employee:list
描述：获取所有员工列表，自动排除管理员角色用户
```

## 排除逻辑

### 判断管理员逻辑
用户被认定为管理员的条件：
- 用户拥有至少一个`is_admin = 1`的角色
- 通过`sys_user_role`表关联查询实现

### SQL实现
```sql
-- 排除管理员用户的查询
SELECT * FROM sys_user u
WHERE u.id NOT IN (
    SELECT ur.user_id
    FROM sys_user_role ur
    JOIN sys_role r ON ur.role_id = r.id
    WHERE r.is_admin = 1 AND ur.is_deleted = 0
)
```

## 配置管理
- 通过角色管理界面可以配置哪些角色是管理员角色
- 支持动态调整，无需重启服务
- 建议在角色管理页面增加"是否管理员"开关控件

## 向后兼容
- 不影响现有API和业务逻辑
- 原有用户查询API保持不变
- 新增专门的员工查询API
- 数据库升级脚本确保平滑迁移

## 使用示例

### 前端调用
```javascript
// 查询员工列表（自动排除管理员）
const response = await api.get('/employee/page', {
  params: {
    pageNum: 1,
    pageSize: 20,
    orgIds: '1,2,3'
  }
});
```

### 角色配置
```javascript
// 角色管理页面新增管理员标记
<el-switch 
  v-model="role.isAdmin" 
  active-text="是" 
  inactive-text="否" 
  @change="updateRoleAdminFlag" 
/>
```

## 部署说明

### 1. 数据库升级
```bash
# 执行数据库升级脚本
mysql -u username -p database_name < database_upgrade_admin_exclude.sql
```

### 2. 应用部署
- 正常部署新版本应用
- 无需额外配置
- 自动生效

### 3. 验证功能
- 访问`/employee/page`接口验证排除功能
- 检查管理员用户不在返回结果中
- 验证普通员工正常显示

## 注意事项

1. **数据一致性**: 确保`is_admin`字段正确初始化
2. **性能考虑**: 大量用户时建议在`sys_user_role.user_id`和`sys_role.is_admin`上建立索引
3. **权限控制**: 员工查询接口需要适当的权限控制
4. **审计日志**: 记录管理员标记的变更操作

## 测试建议

1. **单元测试**: 验证`isAdminUser`方法逻辑
2. **集成测试**: 验证API返回正确的员工列表
3. **性能测试**: 验证大数据量下的查询性能
4. **功能测试**: 验证管理员角色配置变更生效

## 维护指南

1. **角色变更**: 当角色的管理员属性变更时，相关查询会自动生效
2. **用户角色变更**: 用户角色关系变更会实时影响统计结果
3. **监控**: 建议监控员工统计API的性能和准确性 