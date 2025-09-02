# 用户视图模式实施方案

## 🎯 概述
实现管理端用户与管理员分离的切换视图模式，允许用户在同一界面中按类型查看和管理不同用户群体。

## 📋 实施阶段

### ✅ 第一阶段：后端API完善（已完成）

#### 1. Service层扩展
- **ISysUserService**: 新增`listAdminUsersPage`方法
- **SysUserServiceImpl**: 实现管理员用户分页查询
- **SysUserMapper**: 添加管理员查询接口
- **SysUserMapper.xml**: 实现管理员专用SQL查询

#### 2. 门面层增强
- **ISysUserFacade**: 新增`listAdminUsersPage`接口
- **SysUserFacadeImpl**: 实现管理员查询门面层，添加用户类型标识

#### 3. VO对象增强
- **SysUserVO**: 新增`isAdmin`和`userType`字段用于标识用户类型

#### 4. Controller层支持
- **SysUserController**: `/page`接口支持`viewMode`参数
  - `all`: 查询所有用户
  - `employee`: 查询员工（排除管理员）
  - `admin`: 查询管理员

### ✅ 第二阶段：前端类型定义（已完成）

#### 1. TypeScript类型扩展
```typescript
// 用户类型枚举
type UserType = 'ADMIN' | 'EMPLOYEE';

// 视图模式枚举
type ViewMode = 'all' | 'employee' | 'admin';

// User接口增强
interface User {
  // ... 原有字段
  isAdmin?: boolean;
  userType?: UserType;
}

// 搜索参数增强
interface UserSearchParams {
  // ... 原有字段
  viewMode?: ViewMode;
}
```

#### 2. API函数扩展
```typescript
// 新增按视图模式查询的API函数
export function fetchGetUserListByViewMode(
  params?: UserSearchParams & { viewMode?: ViewMode }
): Promise<UserList>
```

### 🔄 第三阶段：前端界面实现（待完成）

#### 1. 视图切换器组件
```vue
<template>
  <div class="view-mode-selector">
    <n-radio-group v-model:value="viewMode" @update:value="handleViewModeChange">
      <n-radio-button value="all">
        <icon-mdi:account-group class="mr-4px text-icon" />
        全部用户
      </n-radio-button>
      <n-radio-button value="employee">
        <icon-mdi:account class="mr-4px text-icon" />
        员工
      </n-radio-button>
      <n-radio-button value="admin">
        <icon-mdi:account-star class="mr-4px text-icon" />
        管理员
      </n-radio-button>
    </n-radio-group>
  </div>
</template>
```

#### 2. 表格列配置
```typescript
// 根据视图模式动态调整列显示
const getColumns = (viewMode: ViewMode) => {
  const baseColumns = [
    // ... 基础列配置
  ];
  
  // 用户类型列
  if (viewMode === 'all') {
    baseColumns.splice(2, 0, {
      key: 'userType',
      title: '类型',
      render: (row) => {
        const isAdmin = row.isAdmin;
        return h(NTag, {
          type: isAdmin ? 'error' : 'success',
          size: 'small'
        }, {
          default: () => isAdmin ? '管理员' : '员工'
        });
      }
    });
  }
  
  // 管理员专属列
  if (viewMode === 'admin') {
    baseColumns.push({
      key: 'adminActions',
      title: '管理权限',
      render: (row) => renderAdminRoles(row)
    });
  }
  
  return baseColumns;
};
```

#### 3. 操作权限控制
```typescript
// 根据视图模式和用户权限控制操作按钮
const getOperations = (viewMode: ViewMode, user: User) => {
  const operations = [];
  
  // 基础操作
  if (hasAuth('sys:user:update')) {
    operations.push({
      key: 'edit',
      label: '编辑',
      handler: () => handleEdit(user)
    });
  }
  
  // 管理员特殊操作
  if (viewMode === 'admin' && hasAuth('sys:user:manage:admin')) {
    operations.push({
      key: 'manageRoles',
      label: '角色管理',
      handler: () => handleManageRoles(user)
    });
  }
  
  // 员工特殊操作
  if (viewMode === 'employee') {
    operations.push({
      key: 'bindDevice',
      label: '绑定设备',
      handler: () => handleBindDevice(user)
    });
  }
  
  return operations;
};
```

### 🔐 第四阶段：权限和安全 ✅

#### 1. 权限配置
```java
// Spring Security权限配置
sys:user:view:all         // 查看所有用户
sys:user:view:employee    // 仅查看员工
sys:user:view:admin       // 仅查看管理员
sys:user:manage:admin     // 管理管理员账户
sys:user:manage:employee  // 管理员工账户
```

#### 2. 前端权限检查
```typescript
// 权限检查钩子
const useUserViewPermission = () => {
  const { hasAuth } = useAuth();
  
  const canViewAll = computed(() => hasAuth('sys:user:view:all'));
  const canViewEmployee = computed(() => hasAuth('sys:user:view:employee'));
  const canViewAdmin = computed(() => hasAuth('sys:user:view:admin'));
  const canManageAdmin = computed(() => hasAuth('sys:user:manage:admin'));
  
  return {
    canViewAll,
    canViewEmployee,
    canViewAdmin,
    canManageAdmin
  };
};
```

## 🚀 技术实现

### 后端架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Controller    │    │     Facade      │    │     Service     │
│                 │    │                 │    │                 │
│ viewMode param  │───▶│ listXxxUsersPage│───▶│ listXxxUsersPage│
│ switch logic    │    │ user type mark  │    │ SQL query       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   SysUserVO     │
                       │                 │
                       │ + isAdmin       │
                       │ + userType      │
                       └─────────────────┘
```

### SQL查询策略
```sql
-- 全部用户
SELECT * FROM sys_user WHERE is_deleted = 0;

-- 仅员工（排除管理员）
SELECT * FROM sys_user su 
WHERE su.id NOT IN (
  SELECT DISTINCT ur.user_id 
  FROM sys_user_role ur 
  JOIN sys_role r ON ur.role_id = r.id 
  WHERE r.is_admin = 1
) AND su.is_deleted = 0;

-- 仅管理员
SELECT * FROM sys_user su 
WHERE EXISTS (
  SELECT 1 FROM sys_user_role ur 
  JOIN sys_role r ON ur.role_id = r.id 
  WHERE ur.user_id = su.id AND r.is_admin = 1
) AND su.is_deleted = 0;
```

### 前端状态管理
```typescript
interface UserManageState {
  viewMode: ViewMode;
  userList: User[];
  loading: boolean;
  searchParams: UserSearchParams;
}

const userManageStore = defineStore('userManage', {
  state: (): UserManageState => ({
    viewMode: 'all',
    userList: [],
    loading: false,
    searchParams: {}
  }),
  
  actions: {
    async fetchUsers() {
      this.loading = true;
      try {
        const { data } = await fetchGetUserListByViewMode({
          ...this.searchParams,
          viewMode: this.viewMode
        });
        this.userList = data.records;
      } finally {
        this.loading = false;
      }
    },
    
    switchViewMode(mode: ViewMode) {
      this.viewMode = mode;
      this.fetchUsers();
    }
  }
});
```

## 🎉 第三阶段完成状态

### 已实现的组件
1. **视图切换器组件** (`user-view-mode-selector.vue`)
   - 支持全部用户、员工、管理员三种视图切换
   - 带有图标和加载状态
   - 响应式设计

2. **增强版表格组件** (`user-page-table-enhanced.vue`)
   - 集成视图切换器
   - 动态列配置（根据视图模式显示不同列）
   - 用户类型标识显示（标签形式）
   - 操作权限控制（基于用户类型和权限）

3. **权限配置文件** (`user-permissions.ts`)
   - 完整的权限常量定义
   - 权限组合配置
   - 动态权限检查函数

### 功能特性
- ✅ 视图模式切换（全部/员工/管理员）
- ✅ 用户类型标识（彩色标签显示）
- ✅ 动态列配置（不同视图显示不同列）
- ✅ 操作权限控制（编辑/删除管理员需要特殊权限）
- ✅ 响应式界面设计
- ✅ 中文友好的界面文字

## 📊 API接口文档

### 用户分页查询（支持视图模式）
```
GET /sys_user/page?viewMode={mode}

参数：
- viewMode: string (可选)
  - all: 查询所有用户
  - employee: 查询员工（排除管理员）
  - admin: 查询管理员

响应：
{
  "code": 200,
  "data": {
    "records": [
      {
        "id": "1",
        "userName": "admin",
        "realName": "系统管理员",
        "isAdmin": true,
        "userType": "ADMIN",
        // ... 其他字段
      }
    ],
    "total": 10,
    "size": 10,
    "current": 1
  }
}
```

## 🔄 数据流转

### 查询流程
```
前端选择视图模式 → API请求带viewMode参数 → Controller路由到对应Service方法 
→ SQL查询对应用户类型 → Facade层标记用户类型 → 返回带类型标识的VO
```

### 权限验证流程
```
用户操作 → 前端权限检查 → API请求 → 后端权限验证 → 业务逻辑执行
```

## 🎨 UI/UX设计

### 视图切换器
- **位置**: 用户管理页面顶部
- **样式**: 单选按钮组，带图标
- **状态**: 切换时显示加载状态

### 用户类型标识
- **管理员**: 红色标签，星星图标
- **员工**: 绿色标签，用户图标
- **全部视图**: 显示类型列，便于区分

### 操作按钮
- **根据用户类型**: 显示不同的操作选项
- **权限控制**: 无权限的操作按钮隐藏或置灰

## 📈 性能优化

### 1. 查询优化
```sql
-- 为角色查询添加索引
CREATE INDEX idx_user_role_admin ON sys_user_role(user_id, role_id);
CREATE INDEX idx_role_admin ON sys_role(is_admin);
```

### 2. 缓存策略
```typescript
// 用户类型缓存，避免重复判断
const userTypeCache = new Map<string, UserType>();

const getUserType = async (userId: string): Promise<UserType> => {
  if (userTypeCache.has(userId)) {
    return userTypeCache.get(userId)!;
  }
  
  const userType = await fetchUserType(userId);
  userTypeCache.set(userId, userType);
  return userType;
};
```

### 3. 分页优化
- **智能分页**: 根据用户类型数量调整默认分页大小
- **懒加载**: 用户类型标识按需加载
- **预加载**: 常用视图数据预加载

## 🧪 测试策略

### 1. 单元测试
```typescript
// 视图模式切换测试
describe('UserViewMode', () => {
  it('should switch to employee view', async () => {
    const store = useUserManageStore();
    await store.switchViewMode('employee');
    expect(store.viewMode).toBe('employee');
    expect(store.userList.every(user => !user.isAdmin)).toBe(true);
  });
});
```

### 2. 集成测试
```java
@Test
public void testViewModeParameter() {
    // 测试全部用户
    mockMvc.perform(get("/sys_user/page?viewMode=all"))
           .andExpect(status().isOk());
    
    // 测试员工视图
    mockMvc.perform(get("/sys_user/page?viewMode=employee"))
           .andExpect(status().isOk());
    
    // 测试管理员视图
    mockMvc.perform(get("/sys_user/page?viewMode=admin"))
           .andExpect(status().isOk());
}
```

### 3. E2E测试
```typescript
// 端到端用户流程测试
describe('User Management E2E', () => {
  it('should allow admin to switch between user views', () => {
    cy.login('admin', 'password');
    cy.visit('/manage/user');
    
    // 切换到员工视图
    cy.get('[data-testid="view-mode-employee"]').click();
    cy.get('[data-testid="user-table"]').should('contain', '员工');
    
    // 切换到管理员视图
    cy.get('[data-testid="view-mode-admin"]').click();
    cy.get('[data-testid="user-table"]').should('contain', '管理员');
  });
});
```

## 🚀 部署和监控

### 1. 配置项
```yaml
# application.yml
ljwx:
  user:
    view-mode:
      enabled: true
      default-mode: all
      cache-enabled: true
      cache-ttl: 300
```

### 2. 监控指标
```java
// Micrometer指标
@Component
public class UserViewMetrics {
    private final Counter viewModeSwitch = Counter.builder("user.view.mode.switch")
            .description("User view mode switch count")
            .tag("mode", "")
            .register(Metrics.globalRegistry);
    
    public void recordViewModeSwitch(String mode) {
        viewModeSwitch.increment(Tags.of("mode", mode));
    }
}
```

## 🔧 故障排查

### 常见问题
1. **视图切换无响应**: 检查前端API调用和后端路由
2. **用户类型显示错误**: 验证`isAdminUser`方法逻辑
3. **权限验证失败**: 检查权限配置和用户角色

### 日志配置
```yaml
logging:
  level:
    com.ljwx.modules.system.facade.impl.SysUserFacadeImpl: DEBUG
    com.ljwx.modules.system.service.impl.SysUserServiceImpl: DEBUG
```

## 📋 总结

这个实施方案通过切换视图模式优雅地解决了管理端用户与管理员分离的需求：

### ✅ 已完成
1. **后端API完善**: 支持三种视图模式查询
2. **数据传输优化**: VO对象增加用户类型标识
3. **类型定义**: 前端TypeScript类型完善

### 🔄 待完成
1. **前端界面实现**: 视图切换器和表格适配
2. **权限控制**: 细粒度权限验证
3. **用户体验**: 界面优化和交互完善

### 🎯 核心优势
- **用户体验**: 统一界面，快速切换
- **开发效率**: 基于现有功能扩展
- **可维护性**: 清晰的代码结构
- **扩展性**: 支持未来用户类型扩展 