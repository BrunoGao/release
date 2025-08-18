# LjwxBoot 后台管理系统

![SpringBoot](https://img.shields.io/badge/Spring%20Boot-3.3-blue.svg)
![JDK](https://img.shields.io/badge/JDK-21+-blue.svg)
![Version](https://img.shields.io/badge/Version-1.0.5--SNAPSHOT-blue.svg)
[![License](https://img.shields.io/badge/License-Apache%20License%202.0-B9D6AF.svg)](./LICENSE)
<br/>
[![Author](https://img.shields.io/badge/Author-brunoGao-green.svg)](https://github.com/brunoGao)
[![Copyright](https://img.shields.io/badge/Copyright-2024%20Zhuang%20Pan%20@LjwxBoot-green.svg)](https://github.com/brunoGao)

### 项目简介


[`LjwxBoot`](https://github.com/brunoGao/ljwx-boot) 是一款现代化的后台管理系统脚手架，它基于 Spring Boot 3
框架进行开发。也得益于前端 [`@SoybeanAdmin 1.0.0`](https://github.com/soybeanjs/soybean-admin)
发版后，精致的用户界面和一致的编码，所以得此顺势完善此项目。
在市面上虽然存在众多出色的 Java 后端管理系统框架，但还是决定重复再造一个轮子。

### 🚀 最新更新

#### v1.0.9 - 分级部门管理权限系统 (2025-08-18)

**🏢 部门层级权限控制架构**
- **通用方法**: 创建 `ISysOrgUnitsService.getTopLevelDeptIdByOrgId()` 通用方法
  - 解析 `sys_org_units.ancestors` 字段（如：`"0,1955920989166800898,1955921028870082561"`）
  - 返回最左边第一个非0数字作为顶级部门ID
  - 支持任意层级部门查找顶级部门

**🔐 岗位管理权限分级控制**
- **分级权限控制**: 基于部门层级的岗位管理权限
  - **顶级部门管理员**: 查看/编辑所有岗位，可使用前端orgId参数
  - **下级部门管理员**: 查看全局岗位+顶级部门岗位，不能编辑
  
- **数据过滤机制**: 基于 `orgId` 和部门层级实现数据隔离
  - **全局岗位**: `orgId = 0`，所有管理员可见
  - **部门岗位**: `orgId = 顶级部门ID`，按权限过滤显示
  - **智能过滤**: 下级部门管理员忽略前端传参，自动基于权限过滤

**📊 健康数据配置分级管理**
- **配置隔离**: 根据 `departmentInfo` 查询顶级部门ID
  - 示例：`departmentInfo=1940374479725170690` → 解析ancestors → 顶级部门ID `1939964806110937090`
  - 从 `t_health_data_config` 表按 `customer_id=顶级部门ID` 过滤配置
  
- **数据一致性**: 确保健康数据显示列与部门权限匹配
  - 不同级别管理员看到不同的数据配置
  - 自动应用对应部门的数据显示规则

**权限判断标准**: 
- 管理员身份: `sys_role.is_admin = 1`
- 部门层级: 通过 `ancestors` 字段解析层级关系
- 顶级部门: `ancestors` 中第一个非0数字对应的部门

**权限矩阵：**
```
├── 顶级部门管理员：全部岗位+健康配置 CRUD
├── 下级部门管理员：受限查看权限（全局+顶级部门数据）
└── 普通用户：无权限
```

**技术实现：**
```
数据可见性 = ancestors解析 → 顶级部门ID → 权限过滤
岗位管理: orgId IN [0, 顶级部门ID]
健康配置: customer_id = 顶级部门ID
```

#### v1.0.8 - 告警通知功能完整实现 (2025-08-16)

**🚨 全新功能：企业级告警通知系统**
- **多渠道通知**: 支持企业微信、公众号微信、系统消息三种通知方式
- **实时推送**: Critical级别告警通过WebSocket实时推送到监控大屏
- **层级通知**: 智能的通知层级体系，确保告警及时到达
  - 用户 → 部门主管 → 租户管理员
  - 如果没有部门管理员，自动上升到租户级管理员
- **配置管理**: 完整的微信告警配置CRUD管理界面
- **大屏集成**: 监控大屏支持告警弹窗、确认操作、音效提醒

**📋 核心特性：**
```
告警规则 → 事件触发 → 多渠道分发
    ↓
├── 微信通知 (企业微信/公众号)
├── 系统消息 (层级分发)  
└── 大屏推送 (Critical告警实时显示)
```

**🎯 技术亮点：**
- **数据库优化**: 清理冗余字段，优化表结构
- **WebSocket实时通信**: Socket.IO支持大屏实时推送
- **权限控制**: 完整的告警配置权限管理
- **容错处理**: 微信通知失败自动降级为消息通知

**📁 相关文件：**
- 后端: `TWechatAlertConfigController.java` - 微信告警配置API
- 前端: `alert/config/index.vue` - 告警配置管理界面  
- 大屏: `ljwx-bigscreen/alert.py` - 增强版告警处理引擎
- 文档: `docs/告警通知功能完整实现方案.md` - 完整技术方案

#### v1.0.7 - 租户/部门权限管理优化 (2025-01-16)

**重要改进：**
- **权限分级控制**: 实现租户和部门的分级权限管理
  - **admin用户**：可以创建租户（顶级组织）+ 创建部门
  - **普通用户**：只能在自己租户下创建部门，无法创建租户
  
- **前端权限控制**: 动态按钮显示
  - 只有admin角色才能看到"新增租户"按钮
  - 普通用户只显示"新增部门"按钮
  
- **后端API安全**: 严格的权限验证
  - 创建顶级组织时检查管理员权限
  - 非admin用户尝试创建租户时返回权限错误

- **文案优化**: 更准确的业务概念
  - "组织" → "租户"：明确多租户架构
  - "新增子组织" → "新增部门"：符合组织层级关系

**权限逻辑：**
```
├── admin用户
│   ├── ✅ 创建租户（顶级组织）
│   └── ✅ 创建部门（子组织）
└── 普通用户  
    ├── ❌ 不能创建租户
    └── ✅ 只能在自己租户下创建部门
```

**🔧 数据库补丁**：执行 [`patch_tenant_permissions.sql`](./patch_tenant_permissions.sql) 添加权限相关字典数据

#### v1.0.6 - 健康数据查询优化 (2025-01-16)

**重要改进：**
- **智能查询策略**: 根据 `userId` 参数自动选择不同的查询逻辑
  - `userId` 为空或 "all"：只查询部门下所有设备的**最新数据**
  - `userId` 为具体值：查询该用户指定时间范围内的**所有数据**
  
- **性能优化**: 解决 n+1 查询问题
  - 新增 `getBatchDailyData()` 和 `getBatchWeeklyData()` 批量查询方法
  - 大幅减少数据库查询次数，提升系统响应速度
  
- **数据安全**: 严格的部门数据隔离
  - 自动过滤管理员设备，防止数据泄露
  - 基于 `departmentInfo` 确保只能访问本部门数据

**API 使用示例：**
```bash
# 查询部门所有设备最新数据
GET /t_user_health_data/page?userId=all&departmentInfo=1940374227169349634

# 查询特定用户时间范围内所有数据  
GET /t_user_health_data/page?userId=12345&departmentInfo=1940374227169349634&startDate=1751299200000&endDate=1755187199999
```

**影响模块：**
- `TUserHealthDataServiceImpl.java` - 核心查询逻辑优化
- `DeviceUserMappingServiceImpl.java` - 设备用户映射服务
- `SysOrgUnitsController.java` - 租户/部门权限控制

### 技术选型

| 技术             | 说明          | 版本         |
|:---------------|:------------|:-----------|
| Spring Boot    | 核心框架        | 3.3.2      |
| MyBatis-Plus   | 持久层框架       | 3.5.6      |
| MySQL          | 数据库         | 8.0.35     |
| Redis          | 缓存          | 7.2.3      |
| Sa-Token       | 鉴权框架        | 1.38.0     |
| Logback        | 日志管理        | 1.5.6      |
| Knife4j        | 接口文档        | 4.5.0      |
| Socket.IO      | WebSocket通信 | 4.7.2      |
| Python Flask   | 告警处理引擎      | 3.x        |
| Lombok         | 工具库         | 1.18.34    |
| Jackson        | JSON解析      | 2.15.4     |
| Gson           | JSON解析      | 2.10.1     |
| Guava          | Google工具库   | 33.2.1-jre |
| Hutool         | 工具库         | 5.8.29     |

### 项目源码

| 名称      | 链接                                                                      |
|:--------|:------------------------------------------------------------------------|
| 前端      | [Panis-admin](https://github.com/brunoGao/panis-admin)               |
| 后端      | [ljwx-boot](https://github.com/brunoGao/ljwx-boot)                 |
| 后端扩展依赖库 | [ljwx-boot-starter](https://github.com/brunoGao/ljwx-boot-starter) |

### 项目启动

##### 前置环境

* **Java** 开发环境 >=JDK 21
* **Java** 开发工具 IDEA
* **Maven** 构建依赖环境 >=3.9.6
* **MySQL** 数据库 >=8.0.35
* **Redis** 缓存数据库 >=7.2.3

##### 克隆项目

```bash
git clone https://github.com/brunoGao/ljwx-boot
git clone https://github.com/brunoGao/ljwx-boot-starter
```

##### 导入启动

1. 将`ljwx-boot`以及`ljwx-boot-starter`分别导出到IDEA中，等待 Maven 依赖下载完成
2. 创建数据库`panis_boot`，导入`ljwx-boot-doc`项目中的`panis_boot.sql`，文件[暂在QQ群获取](https://github.com/brunoGao/ljwx-boot/issues/5)
3. 修改`ljwx-boot`项目中的`application-dev.yml`文件中的`数据库`以及`Redis`连接信息
4. 启动`LjwxBootApplication`类
5. 看到`---[LjwxBoot]-[ljwx-boot-admin]-启动完成，当前使用的端口:[9999]，环境变量:[mybatis,dev]---`即代表启动成功

### 📊 数据字典SQL

系统使用数据字典来管理下拉选项、状态值等基础数据。以下是核心数据字典表的建表SQL：

#### 字典主表 (sys_dict)
```sql
CREATE TABLE `sys_dict` (
  `id` bigint NOT NULL COMMENT 'ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '字典名称',
  `code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '字典编码',
  `type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '字典类型(1:系统字典,2:业务字典)',
  `sort` int DEFAULT NULL COMMENT '排序值',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '字典描述',
  `status` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '1' COMMENT '是否启用(0:禁用,1:启用)',
  `create_user` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '创建用户名称',
  `create_user_id` bigint DEFAULT NULL COMMENT '创建用户ID',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_user` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '更新用户名称',
  `update_user_id` bigint DEFAULT NULL COMMENT '更新用户ID',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `is_deleted` tinyint DEFAULT '0' COMMENT '是否删除(0:否,1:是)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据字典主表';
```

#### 字典子项表 (sys_dict_item)
```sql
CREATE TABLE `sys_dict_item` (
  `id` bigint NOT NULL COMMENT 'ID',
  `dict_id` bigint DEFAULT NULL COMMENT '父字典ID',
  `dict_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '父字典编码',
  `value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '数据值',
  `zh_cn` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '中文名称',
  `en_us` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '英文名称',
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '类型(前端渲染类型)',
  `sort` int DEFAULT NULL COMMENT '排序值',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '字典描述',
  `status` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '1' COMMENT '是否启用(0:禁用,1:启用)',
  `create_user` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '创建用户名称',
  `create_user_id` bigint DEFAULT NULL COMMENT '创建用户ID',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_user` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '更新用户名称',
  `update_user_id` bigint DEFAULT NULL COMMENT '更新用户ID',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `is_deleted` tinyint DEFAULT '0' COMMENT '是否删除(0:否,1:是)',
  PRIMARY KEY (`id`),
  KEY `idx_dict_code` (`dict_code`),
  KEY `idx_dict_id` (`dict_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据字典子项表';
```

#### 基础字典数据
```sql
-- 状态字典
INSERT INTO `sys_dict` (`id`, `name`, `code`, `type`, `sort`, `description`, `status`) VALUES 
(1, '状态', 'status', '1', 1, '通用状态字典', '1');

INSERT INTO `sys_dict_item` (`id`, `dict_id`, `dict_code`, `value`, `zh_cn`, `en_us`, `type`, `sort`, `description`, `status`) VALUES 
(1, 1, 'status', '0', '禁用', 'Disabled', 'error', 1, '禁用状态', '1'),
(2, 1, 'status', '1', '启用', 'Enabled', 'success', 2, '启用状态', '1');

-- 用户状态字典  
INSERT INTO `sys_dict` (`id`, `name`, `code`, `type`, `sort`, `description`, `status`) VALUES 
(2, '用户状态', 'user_status', '1', 2, '用户状态字典', '1');

INSERT INTO `sys_dict_item` (`id`, `dict_id`, `dict_code`, `value`, `zh_cn`, `en_us`, `type`, `sort`, `description`, `status`) VALUES 
(3, 2, 'user_status', '0', '禁用', 'Disabled', 'error', 1, '用户禁用', '1'),
(4, 2, 'user_status', '1', '正常', 'Normal', 'success', 2, '用户正常', '1'),
(5, 2, 'user_status', '2', '锁定', 'Locked', 'warning', 3, '用户锁定', '1');

-- 字典类型字典
INSERT INTO `sys_dict` (`id`, `name`, `code`, `type`, `sort`, `description`, `status`) VALUES 
(3, '字典类型', 'dict_type', '1', 3, '字典类型分类', '1');

INSERT INTO `sys_dict_item` (`id`, `dict_id`, `dict_code`, `value`, `zh_cn`, `en_us`, `type`, `sort`, `description`, `status`) VALUES 
(6, 3, 'dict_type', '1', '系统字典', 'System Dict', 'primary', 1, '系统内置字典', '1'),
(7, 3, 'dict_type', '2', '业务字典', 'Business Dict', 'info', 2, '业务定制字典', '1');
```

### 项目结构

```
LjwxBoot
├── ljwx-boot-common -- 基础模块
├── ljwx-boot-admin -- 后台管理模块
│   └── controller  -- 控制层
├── ljwx-boot-infrastructure -- 基础配置
├── ljwx-boot-modules -- 业务模块
│   └── system 
│       └── repository -- 数据交互
│           └── mapper -- 持久层
│       └── domain  -- 业务模型
│           └── entity -- 数据库实体
│           └── vo -- 视图对象
│           └── bo -- 业务对象
│           └── dto -- 传输对象
│       └── service -- 服务层
│           └── impl -- 服务实现层
│       └── facade -- 门面层
│           └── impl -- 门面实现层
│   └── base -- 基础管理
│   └── ... -- 其他模块
└── pom.xml -- 公共依赖
```

#### `common` 和 `infrastructure` 区别

* `common`模块：通常包含通用的工具类、异常定义、常量定义等与业务无关的代码。这些代码可以被整个应用程序共享。
    - 通用工具类，比如日期处理、字符串处理等
    - 通用异常定义，比如业务异常、参数校验异常等
    - 通用常量定义，比如状态码、错误信息等

* `infrastructure`模块：通常包含与基础设施相关的代码，比如数据库访问、缓存、消息队列、配置管理等。这些代码通常是为了支持业务模块的运行而存在的。
    - 数据访问相关的代码，比如数据库连接、ORM框架配置、数据源配置等
    - 缓存相关的代码，比如缓存配置、缓存管理等
    - 消息队列相关的代码，比如消息生产者、消费者配置等
    - 配置管理相关的代码，比如配置加载、动态配置更新等

对于静态类、工具类、异常定义等，你可以根据其功能和作用来判断放入`common`还是`infrastructure`
模块。如果它们是通用的、与业务无关的，可以放入`common`模块；如果它们是为了支持业务模块的基础设施，可以放入`infrastructure`模块。

### 特别鸣谢

- [SoybeanJS](https://github.com/soybeanjs)
- [MyBatis-Plus](https://mybatis.plus/)
- [Sa-Token](https://sa-token.cc/)
- [Knife4j](https://doc.xiaominfo.com/)
- [HuTool](https://hutool.cn/)
- 不一一列举，感谢所有开源项目的贡献者

### 开源协议

项目基于 [Apache License 2.0 © 2024 Zhuang Pan](./LICENSE) 协议，仅供学习参考，商业使用请遵循作者版权信息，作者不保证也不承担任何软件的使用风险。