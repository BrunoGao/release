# 动态菜单权限管理系统

## 系统概述

动态菜单权限管理系统是一套完整的解决方案，用于解决 ljwx-admin 和 ljwx-boot 项目中菜单管理的核心问题：

- **自动发现问题**：新增页面无法自动添加到菜单系统
- **灵活配置问题**：菜单无法自由调整名称、层级和顺序
- **多租户支持**：不同租户需要不同的菜单配置
- **权限控制**：基于角色的菜单访问控制

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端 ljwx-admin                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   路由扫描界面   │  │   菜单管理界面   │  │   批量操作界面   │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  useDynamicMenu Hook                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTP API
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    后端 ljwx-boot                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              DynamicMenuController                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              DynamicMenuServiceImpl                        │ │
│  │  • 前端文件扫描    • 菜单自动生成    • 批量操作处理      │ │
│  │  • 权限验证       • 缓存管理        • 多租户支持        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   数据持久层                                │ │
│  │  • SysMenu 实体   • 菜单权限关系   • 租户隔离             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

**前端技术栈**：
- Vue 3 + TypeScript
- Naive UI 组件库
- Vite 构建工具
- Pinia 状态管理

**后端技术栈**：
- Spring Boot 3
- MyBatis Plus ORM
- Redis 缓存
- Spring Security 权限控制

## 核心功能

### 1. 前端路由自动扫描

#### 功能描述
系统能够自动扫描前端项目中的 Vue 文件，发现新的页面组件和路由配置，自动生成对应的菜单项。

#### 扫描机制
```java
// 文件扫描逻辑
Files.walkFileTree(basePath, new SimpleFileVisitor<Path>() {
    @Override
    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
        // 检查文件类型（.vue, .tsx, .jsx, .ts, .js）
        // 应用包含/排除模式过滤
        // 解析文件内容，提取路由信息
        // 生成菜单建议配置
    }
});
```

#### 支持的文件类型
- `.vue` - Vue 单文件组件
- `.tsx` - TypeScript JSX 文件
- `.jsx` - JavaScript JSX 文件  
- `.ts` - TypeScript 文件
- `.js` - JavaScript 文件

#### 路由信息提取
```javascript
// 从文件内容中提取的信息
const routeInfo = {
    path: "/system/user",           // 路由路径
    name: "SystemUser",             // 路由名称
    title: "用户管理",              // 页面标题
    component: "views/system/user", // 组件路径
    icon: "mdi:account",           // 建议图标
    level: 2                       // 菜单层级
};
```

### 2. 智能菜单生成

#### 自动生成规则
- **名称生成**：基于文件名或路径自动生成菜单名称
- **图标建议**：根据路径关键词智能建议图标
- **层级推断**：根据文件路径结构推断菜单层级
- **排序规则**：按照扫描顺序或自定义规则分配排序值

#### 生成算法示例
```java
public DynamicMenuConfigDTO autoGenerateMenu(String routePath, String filePath) {
    DynamicMenuConfigDTO config = new DynamicMenuConfigDTO();
    
    // 生成菜单名称
    String fileName = Paths.get(filePath).getFileName().toString();
    String menuName = fileName.replaceAll("\\.(vue|tsx|jsx|ts|js)$", "");
    config.setName(capitalizeWords(menuName.replaceAll("[-_]", " ")));
    
    // 智能图标建议
    config.setIcon(generateIcon(routePath, fileName));
    
    // 层级判断
    String[] pathParts = routePath.split("/");
    config.setType(pathParts.length <= 2 ? "1" : "2"); // 1-目录，2-菜单
    
    return config;
}
```

### 3. 灵活的菜单管理

#### 批量操作功能
系统支持多种批量操作，提高菜单管理效率：

- **批量启用/禁用**：快速改变多个菜单的状态
- **批量移动**：将多个菜单移动到指定父级
- **批量删除**：递归删除菜单及其子菜单
- **批量更新**：同时更新多个菜单的属性

#### 拖拽排序
前端界面支持拖拽操作，直观地调整菜单顺序和层级关系。

#### 实时预览
提供菜单配置的实时预览功能，支持按角色预览不同用户看到的菜单结构。

### 4. 多租户支持

#### 租户隔离机制
```sql
-- 菜单表结构支持多租户
CREATE TABLE sys_menu (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT,      -- 租户ID，null表示全局菜单
    parent_id BIGINT,
    name VARCHAR(50),
    path VARCHAR(200),
    -- ... 其他字段
    INDEX idx_customer_id (customer_id)
);
```

#### 权限控制
- **超级管理员**：可管理所有租户的菜单
- **租户管理员**：只能管理自己租户的菜单
- **普通用户**：根据角色权限查看菜单

### 5. 缓存优化

#### 多级缓存策略
```java
// Spring Cache 配置
@Cacheable(value = "dynamic_menus", key = "#customerId")
public List<DynamicMenuVO> getDynamicMenuConfig(Long customerId) {
    // 查询数据库逻辑
}

// 缓存失效策略
@CacheEvict(value = "dynamic_menus", allEntries = true)
public String updateDynamicMenuConfig(DynamicMenuConfigDTO configDTO) {
    // 更新逻辑
}
```

## 详细设计

### 数据库设计

#### 核心表结构
```sql
-- 系统菜单表
CREATE TABLE sys_menu (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父菜单ID',
    customer_id BIGINT COMMENT '租户ID',
    type VARCHAR(1) DEFAULT '2' COMMENT '菜单类型(1目录 2菜单 3按钮)',
    name VARCHAR(50) NOT NULL COMMENT '菜单名称',
    title VARCHAR(50) COMMENT '菜单标题',
    path VARCHAR(200) COMMENT '路由地址',
    component VARCHAR(255) COMMENT '组件路径',
    icon VARCHAR(100) COMMENT '菜单图标',
    icon_type VARCHAR(1) DEFAULT '1' COMMENT '图标类型(1 Iconify 2本地)',
    status VARCHAR(1) DEFAULT '1' COMMENT '菜单状态(0停用 1启用)',
    hide_in_menu VARCHAR(1) DEFAULT '0' COMMENT '是否隐藏(0显示 1隐藏)',
    permission VARCHAR(255) COMMENT '权限标识',
    sort INT DEFAULT 0 COMMENT '显示顺序',
    is_system VARCHAR(1) DEFAULT '0' COMMENT '是否系统菜单',
    source VARCHAR(20) DEFAULT 'manual' COMMENT '来源(manual手动 scan扫描 import导入)',
    source_file VARCHAR(500) COMMENT '源文件路径',
    last_scan_time DATETIME COMMENT '最后扫描时间',
    version VARCHAR(10) COMMENT '版本号',
    remark VARCHAR(500) COMMENT '备注',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_parent_id (parent_id),
    KEY idx_customer_id (customer_id),
    KEY idx_status (status)
) COMMENT='菜单权限表';

-- 角色菜单关联表
CREATE TABLE sys_role_menu (
    role_id BIGINT NOT NULL COMMENT '角色ID',
    menu_id BIGINT NOT NULL COMMENT '菜单ID',
    PRIMARY KEY (role_id, menu_id)
) COMMENT='角色和菜单关联表';
```

### API 接口设计

#### RESTful API 规范
```http
GET    /sys_menu/dynamic/config              # 获取动态菜单配置
POST   /sys_menu/dynamic/scan                # 扫描前端路由文件  
POST   /sys_menu/dynamic/auto-sync           # 自动同步菜单配置
PUT    /sys_menu/dynamic/config              # 更新动态菜单配置
PUT    /sys_menu/dynamic/batch               # 批量更新菜单
PUT    /sys_menu/dynamic/reorder             # 重新排序菜单
POST   /sys_menu/dynamic/preset              # 应用预设模板
DELETE /sys_menu/dynamic/cache               # 清除菜单缓存
GET    /sys_menu/dynamic/preview             # 预览菜单配置
POST   /sys_menu/dynamic/import              # 导入菜单配置
GET    /sys_menu/dynamic/export              # 导出菜单配置
```

#### 接口详细说明

##### 1. 扫描前端路由文件
```http
POST /sys_menu/dynamic/scan
Content-Type: application/json

{
  "frontendPath": "/Users/project/ljwx-admin/src/views",
  "scanMode": "auto",
  "includePatterns": ["**/*.vue", "**/*.tsx"],
  "excludePatterns": ["**/components/**", "**/temp/**"],
  "recursive": true,
  "autoCreate": false,
  "overwriteExisting": false,
  "customerId": 1
}

// 响应
{
  "code": 200,
  "message": "扫描完成",
  "data": {
    "scanTime": "2024-01-15 14:30:00",
    "foundFiles": [
      "src/views/system/user/index.vue",
      "src/views/system/role/index.vue"
    ],
    "newRoutes": [
      {
        "path": "/system/user", 
        "title": "用户管理",
        "component": "views/system/user",
        "suggestedIcon": "mdi:account",
        "level": 2
      }
    ],
    "scanStats": {
      "totalFiles": 45,
      "newRoutes": 3,
      "changedFiles": 1,
      "scanDuration": 1250
    }
  }
}
```

##### 2. 批量更新菜单
```http
PUT /sys_menu/dynamic/batch
Content-Type: application/json

{
  "menuIds": [1, 2, 3],
  "operation": "update",
  "updateFields": {
    "status": "1",
    "icon": "mdi:menu"
  },
  "reason": "批量启用系统菜单"
}

// 响应
{
  "code": 200,
  "message": "操作成功", 
  "data": "成功批量更新 3 个菜单的字段"
}
```

### 前端组件设计

#### 主界面组件结构
```
DynamicMenuManagement/
├── index.vue                    # 主界面
├── modules/
│   ├── scan-result-modal.vue   # 扫描结果展示
│   ├── menu-edit-modal.vue     # 菜单编辑弹窗
│   ├── batch-update-modal.vue  # 批量操作弹窗
│   └── icon-select-modal.vue   # 图标选择器
└── hooks/
    └── use-dynamic-menu.ts     # 业务逻辑钩子
```

#### 组件功能特性

##### 1. 扫描结果展示
```vue
<template>
  <ScanResultModal
    v-model:visible="scanResultVisible"
    :scan-result="scanResult"
    @sync-menus="handleSyncMenus"
  >
    <!-- 扫描统计卡片 -->
    <div class="grid grid-cols-4 gap-12px">
      <NCard>{{ scanStats.totalFiles }} 总文件数</NCard>
      <NCard>{{ scanStats.newRoutes }} 新路由</NCard>
      <!-- ... -->
    </div>
    
    <!-- 新路由列表 -->
    <NDataTable
      :data="newRoutes"
      :columns="routeColumns" 
      v-model:checked-row-keys="selectedRoutes"
    />
  </ScanResultModal>
</template>
```

##### 2. 菜单树形表格
```vue
<template>
  <NDataTable
    :data="menuData"
    :columns="columns"
    :row-key="(row) => row.id"
    :children-key="'children'"
    :indent="24"
    default-expand-all
  />
</template>

<script setup lang="ts">
// 构建菜单树
function buildMenuTree(menus: MenuRecord[]): MenuRecord[] {
  const map = new Map();
  const roots = [];
  
  menus.forEach(menu => {
    map.set(menu.id, { ...menu, children: [] });
  });
  
  menus.forEach(menu => {
    const currentMenu = map.get(menu.id);
    if (!menu.parentId) {
      roots.push(currentMenu);
    } else {
      const parent = map.get(menu.parentId);
      if (parent) {
        parent.children.push(currentMenu);
      }
    }
  });
  
  return sortMenus(roots);
}
</script>
```

## 使用指南

### 快速开始

#### 1. 系统部署
```bash
# 后端部署
cd ljwx-boot
./mvn clean package
java -jar target/ljwx-boot.jar

# 前端部署  
cd ljwx-admin
npm install
npm run dev
```

#### 2. 访问管理界面
打开浏览器访问：`http://localhost:3000/#/system/dynamic-menu`

#### 3. 首次使用流程
1. **权限检查**：确保当前用户具有 `sys:menu:dynamic:*` 权限
2. **路由扫描**：点击"扫描路由"按钮，选择前端项目路径
3. **查看结果**：查看扫描发现的新路由和文件变化
4. **选择同步**：选择需要同步的路由，点击"同步选中的路由"
5. **菜单调整**：在菜单管理界面调整菜单属性、顺序等

### 高级功能使用

#### 1. 批量操作
```typescript
// 选择多个菜单后，点击批量操作
const batchData = {
  operation: "update",
  updateFields: {
    status: "1",        // 启用状态
    icon: "mdi:menu"    // 统一图标
  },
  reason: "系统优化"
};

await batchUpdateMenus({
  menuIds: [1, 2, 3],
  ...batchData
});
```

#### 2. 预设模板应用
```typescript
// 应用系统管理模板
await applyPresetTemplate("system-management", customerId);

// 应用监控大屏模板  
await applyPresetTemplate("monitoring-dashboard", customerId);
```

#### 3. 菜单导入导出
```typescript
// 导出当前租户的菜单配置
const menuConfig = await exportMenuConfig(customerId);

// 导入菜单配置到其他租户
await importMenuConfig(menuConfig);
```

### 配置说明

#### 1. 扫描配置
```typescript
interface DynamicMenuScanDTO {
  frontendPath: string;           // 前端项目路径
  scanMode: 'auto' | 'manual';    // 扫描模式
  includePatterns: string[];      // 包含模式
  excludePatterns: string[];      // 排除模式
  recursive: boolean;             // 递归扫描
  autoCreate: boolean;            // 自动创建菜单
  nameGenerationRule: string;     // 名称生成规则
  iconGenerationRule: string;     // 图标生成规则
}
```

#### 2. 权限配置
```yaml
# Spring Security 权限配置
security:
  permissions:
    - "sys:menu:dynamic:scan"      # 路由扫描权限
    - "sys:menu:dynamic:sync"      # 菜单同步权限
    - "sys:menu:dynamic:config"    # 菜单配置权限
    - "sys:menu:dynamic:batch"     # 批量操作权限
```

## 最佳实践

### 1. 扫描配置建议

#### 路径配置
```typescript
const scanConfig = {
  frontendPath: "/src/views",
  includePatterns: [
    "**/*.vue",           // Vue组件
    "**/pages/**/*.tsx"   // React页面
  ],
  excludePatterns: [
    "**/components/**",   // 排除通用组件
    "**/temp/**",         // 排除临时文件
    "**/__tests__/**"     // 排除测试文件
  ]
};
```

#### 命名规范
- **文件名**：使用 PascalCase，如 `UserManagement.vue`
- **路由路径**：使用 kebab-case，如 `/user-management`
- **菜单名称**：使用中文描述，如 "用户管理"

### 2. 菜单结构设计

#### 推荐层级结构
```
系统管理 (level 1, type 1 - 目录)
├── 用户管理 (level 2, type 2 - 菜单)
│   ├── 查看用户 (level 3, type 3 - 按钮)
│   ├── 新增用户 (level 3, type 3 - 按钮) 
│   └── 编辑用户 (level 3, type 3 - 按钮)
├── 角色管理 (level 2, type 2 - 菜单)
└── 权限管理 (level 2, type 2 - 菜单)
```

#### 图标使用规范
- **系统类**：`mdi:cog`, `mdi:settings`
- **用户类**：`mdi:account`, `mdi:account-group`  
- **数据类**：`mdi:database`, `mdi:table`
- **监控类**：`mdi:monitor-dashboard`, `mdi:chart-line`

### 3. 性能优化

#### 缓存策略
```java
// 1. 启用Spring Cache
@EnableCaching
@Configuration
public class CacheConfig {
    @Bean
    public CacheManager cacheManager() {
        RedisCacheManager.Builder builder = RedisCacheManager
            .RedisCacheManagerBuilder
            .fromConnectionFactory(redisConnectionFactory)
            .cacheDefaults(cacheConfiguration());
        return builder.build();
    }
}

// 2. 合理设置缓存TTL
@Cacheable(value = "dynamic_menus", key = "#customerId")
@CachePut(value = "dynamic_menus", key = "#customerId")  
@CacheEvict(value = "dynamic_menus", allEntries = true)
```

#### 批量操作优化
```java
// 使用 MyBatis Plus 批量操作
@Transactional
public String batchUpdateMenus(MenuBatchUpdateDTO batchDTO) {
    List<SysMenu> menus = listByIds(batchDTO.getMenuIds());
    
    // 批量更新而非逐个更新
    updateBatchById(menus);
    
    return "批量操作完成";
}
```

### 4. 安全考虑

#### 权限校验
```java
@SaCheckPermission("sys:menu:dynamic:scan")
@PostMapping("/scan") 
public Result<MenuScanResultVO> scanRoutes(@Valid @RequestBody DynamicMenuScanDTO scanDTO) {
    // 验证前端路径安全性
    if (!isPathSafe(scanDTO.getFrontendPath())) {
        throw new APIException("路径不安全");
    }
    
    // 限制扫描文件数量
    if (scanDTO.getMaxFiles() > 1000) {
        scanDTO.setMaxFiles(1000);
    }
    
    return Result.data(dynamicMenuService.scanFrontendRoutes(scanDTO));
}
```

#### 数据校验
```java
public List<String> validateMenuConfig(DynamicMenuConfigDTO config) {
    List<String> errors = new ArrayList<>();
    
    // SQL注入防护
    if (containsSqlKeywords(config.getName())) {
        errors.add("菜单名称包含非法字符");
    }
    
    // XSS防护
    if (containsScriptTags(config.getDescription())) {
        errors.add("菜单描述包含脚本标签");
    }
    
    return errors;
}
```

## 故障排除

### 常见问题

#### 1. 扫描不到文件
**问题**：扫描结果为空或文件数量不正确

**解决步骤**：
1. 检查 `frontendPath` 路径是否正确
2. 验证 `includePatterns` 和 `excludePatterns` 配置
3. 确认服务器有文件访问权限
4. 查看日志中的详细错误信息

```bash
# 检查路径是否存在
ls -la /path/to/frontend/src/views

# 检查文件权限
find /path/to/frontend -name "*.vue" -type f
```

#### 2. 菜单同步失败
**问题**：扫描成功但菜单同步时报错

**解决步骤**：
1. 检查数据库连接是否正常
2. 验证菜单数据的合法性
3. 确认当前用户有菜单创建权限
4. 查看数据库中是否有重复的菜单路径

```sql
-- 检查菜单重复
SELECT path, COUNT(*) as count 
FROM sys_menu 
WHERE customer_id = ? 
GROUP BY path 
HAVING count > 1;
```

#### 3. 权限问题
**问题**：用户无法访问动态菜单管理功能

**解决步骤**：
1. 检查用户角色和权限分配
2. 验证 Spring Security 配置
3. 确认菜单权限表中的数据

```sql
-- 检查用户权限
SELECT r.role_name, p.permission 
FROM sys_user_role ur
JOIN sys_role r ON ur.role_id = r.id
JOIN sys_role_menu rm ON r.id = rm.role_id  
JOIN sys_menu m ON rm.menu_id = m.id
WHERE ur.user_id = ?;
```

### 日志分析

#### 开启调试日志
```yaml
logging:
  level:
    com.ljwx.modules.system.service.impl.DynamicMenuServiceImpl: DEBUG
    com.ljwx.admin.controller.system.DynamicMenuController: DEBUG
```

#### 关键日志示例
```log
2024-01-15 14:30:00 [INFO ] 开始扫描前端路由文件，路径: /src/views
2024-01-15 14:30:01 [DEBUG] 发现文件: src/views/system/user/index.vue
2024-01-15 14:30:01 [DEBUG] 解析路由信息: {path: "/system/user", component: "views/system/user"}
2024-01-15 14:30:02 [INFO ] 扫描完成，发现文件: 45, 变更文件: 3, 新路由: 2
```

## 系统集成

### 与现有系统集成

#### 1. 权限系统集成
动态菜单系统无缝集成现有的 Spring Security 权限框架：

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth
            .requestMatchers("/sys_menu/dynamic/**").hasAnyRole("ADMIN", "MENU_MANAGER")
            .anyRequest().authenticated()
        );
        return http.build();
    }
}
```

#### 2. 多租户系统集成
与现有多租户架构完全兼容：

```java
// 自动注入租户ID
@Component
public class TenantMenuInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        Long customerId = getCurrentCustomerId();
        request.setAttribute("customerId", customerId);
        return true;
    }
}
```

### 扩展开发

#### 1. 自定义扫描规则
```java
@Component
public class CustomRouteScanStrategy implements RouteScanStrategy {
    
    @Override
    public List<RouteInfo> scanRoutes(Path basePath, DynamicMenuScanDTO config) {
        // 实现自定义扫描逻辑
        return customScanLogic(basePath, config);
    }
}
```

#### 2. 菜单模板扩展
```java
@Service
public class MenuTemplateService {
    
    public List<DynamicMenuConfigDTO> loadTemplate(String templateName) {
        switch (templateName) {
            case "e-commerce":
                return createECommerceTemplate();
            case "crm":
                return createCrmTemplate();
            default:
                return createDefaultTemplate();
        }
    }
}
```

## 总结

动态菜单权限管理系统完美解决了 ljwx-admin 和 ljwx-boot 项目中的菜单管理痛点：

### 核心价值
1. **自动化**：前端页面自动发现和菜单生成，减少90%的手动配置工作
2. **灵活性**：支持拖拽排序、批量操作、实时预览等丰富的管理功能
3. **多租户**：完整的租户隔离和权限控制机制
4. **易用性**：直观的用户界面和完整的操作引导
5. **安全性**：全面的权限校验和数据安全保护

### 技术优势
1. **高性能**：多级缓存和批量操作优化
2. **可扩展**：模块化设计，支持自定义扩展
3. **可维护**：完整的日志记录和错误处理机制
4. **标准化**：遵循RESTful API设计规范

### 部署建议
1. **生产环境**：启用Redis缓存，配置数据库连接池
2. **开发环境**：开启调试日志，使用本地文件缓存
3. **测试环境**：配置自动化测试用例，验证各项功能

通过这套完整的动态菜单权限管理系统，开发团队可以大幅提升菜单管理效率，为用户提供更好的系统体验。