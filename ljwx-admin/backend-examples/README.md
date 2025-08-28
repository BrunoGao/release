# 多租户权限系统实现指南

## 概述

本目录包含了实现多租户权限系统的后端示例代码和数据库迁移脚本。

## 权限架构设计

### 1. 用户角色层级

- **admin（超级管理员）**：
  - 可以管理所有租户
  - 可以创建、修改、删除任何租户的角色和岗位
  - 可以查看全局角色和所有租户角色
  
- **租户管理员（R_ADMIN角色）**：
  - 只能管理自己租户内的用户、部门、角色、岗位
  - 不能创建新租户
  - 不能查看其他租户的数据

- **普通用户**：
  - 只能访问分配给自己的功能
  - 受角色和权限控制

### 2. 数据库设计

#### sys_role 表字段
```sql
- id: 主键
- role_name: 角色名称
- role_code: 角色编码
- description: 角色描述
- status: 状态（1启用，0禁用）
- sort: 排序
- is_admin: 是否管理员角色
- customer_id: 租户ID（NULL表示全局角色）
- create_time: 创建时间
- update_time: 更新时间
```

#### sys_position 表字段
```sql
- id: 主键
- name: 岗位名称
- code: 岗位编码
- abbr: 岗位简称
- description: 岗位描述
- sort: 排序
- status: 状态
- org_id: 组织ID
- weight: 权重
- customer_id: 租户ID（NULL表示全局岗位）
- create_time: 创建时间
- update_time: 更新时间
```

## 实现文件说明

### 1. TenantRoleService.java
租户角色管理服务，主要功能：
- 为新租户创建默认角色和岗位
- 根据用户权限查询角色/岗位列表
- 支持多租户数据隔离

### 2. OrgUnitsChangeListener.java
组织架构变更监听器，主要功能：
- 监听租户创建事件，自动同步默认数据
- 监听租户删除事件，清理相关数据
- 事件驱动的数据同步机制

### 3. DatabaseMigration.sql
数据库迁移脚本，主要内容：
- 为现有表添加 customer_id 字段
- 创建必要的索引优化查询性能
- 插入默认的全局角色数据

## 前端实现要点

### 1. 权限判断逻辑
```javascript
// 判断是否是超级管理员（admin用户，可以管理所有租户）
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

// 判断是否是租户管理员（只能管理自己租户）
const isTenantAdmin = computed(() => {
  return authStore.userInfo?.roleIds?.includes('R_ADMIN') && !isAdmin.value;
});
```

### 2. API 参数处理
```javascript
// 角色查询参数
apiParams: {
  page: 1,
  pageSize: 20,
  status: null,
  roleName: null,
  roleCode: null,
  // 非admin用户只查看自己租户的角色
  customerId: isAdmin.value ? null : currentCustomerId
}
```

### 3. UI 组件差异化显示
```vue
<!-- 只有admin用户才显示租户列 -->
...(isAdmin.value ? [{
  key: 'customerId',
  title: '租户ID',
  align: 'center',
  width: 100,
  render: row => row.customerId || '全局'
}] : [])

<!-- 只有admin用户才能选择租户 -->
<NFormItem v-if="isAdmin" label="租户" path="customerId">
  <NInputNumber 
    v-model:value="model.customerId" 
    placeholder="留空为全局角色" 
    :show-button="false"
    clearable
  />
</NFormItem>
```

## 部署步骤

### 1. 数据库迁移
```bash
# 执行数据库迁移脚本
mysql -u username -p database_name < DatabaseMigration.sql
```

### 2. 后端代码部署
1. 将 `TenantRoleService.java` 复制到对应的 service 包
2. 将 `OrgUnitsChangeListener.java` 复制到对应的 listener 包
3. 根据实际项目结构调整包名和依赖

### 3. 前端代码部署
前端代码已经直接在现有文件中修改完成，包括：
- 权限判断逻辑更新
- 角色管理页面多租户支持
- 岗位管理页面多租户支持
- 组织架构管理权限控制

## 测试验证

### 1. 功能测试
- [ ] admin用户可以查看所有租户的角色和岗位
- [ ] admin用户可以创建全局角色和特定租户的角色
- [ ] 租户管理员只能查看和管理自己租户的数据
- [ ] 创建新租户时自动生成默认角色和岗位

### 2. 权限测试
- [ ] 租户A的管理员无法访问租户B的数据
- [ ] 普通用户无法访问管理功能
- [ ] admin用户可以跨租户操作

### 3. 性能测试
- [ ] 大量租户数据下的查询性能
- [ ] 索引是否正确创建和使用
- [ ] 并发操作的数据一致性

## 注意事项

1. **数据安全**：确保租户数据隔离，防止数据泄露
2. **性能优化**：合理使用索引，避免全表扫描
3. **事务处理**：租户创建和角色同步需要在事务中完成
4. **错误处理**：完善的异常处理和补偿机制
5. **审计日志**：记录重要操作的审计日志

## 扩展功能

1. **角色模板**：预定义不同行业的角色模板
2. **权限继承**：支持角色间的权限继承关系
3. **动态权限**：支持运行时动态调整权限
4. **权限审计**：完整的权限变更审计功能