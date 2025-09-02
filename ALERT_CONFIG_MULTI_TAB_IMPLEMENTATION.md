# 告警配置多租户三标签页实现方案

## 项目概述

为ljwx-admin系统实现了一个全新的告警配置管理页面，支持企业微信、微信公众号、消息配置三个标签页的独立管理，并具备完整的多租户支持。

## 🎯 功能特性

### 1. 三标签页架构
- **企业微信配置**：管理企业微信告警通知配置
- **微信公众号配置**：管理微信公众号告警通知配置  
- **消息配置**：管理短信、邮件、Webhook、站内消息等通知配置

### 2. 多租户支持
- 所有配置表都支持`customer_id`字段进行租户隔离
- 自动根据当前登录用户的`customerId`进行数据过滤
- 确保不同租户间的配置完全隔离

### 3. 完整CRUD操作
- 新增配置：支持各种类型的告警配置创建
- 编辑配置：可修改现有配置信息
- 删除配置：支持单条和批量删除
- 查询配置：支持条件搜索和分页

## 📁 文件结构

```
ljwx-admin/src/views/alert/config/
├── index.vue                                    # 主页面（三标签页容器）
└── modules/
    ├── alertconfigwechat-search.vue             # 微信配置搜索组件
    ├── alert-config-wechat-operate-drawer.vue   # 微信配置操作抽屉
    ├── message-config-search.vue                # 消息配置搜索组件  
    └── message-config-operate-drawer.vue        # 消息配置操作抽屉
```

## 🗄️ 数据库表结构

### 1. 微信告警配置表 (t_wechat_alarm_config)

```sql
CREATE TABLE `t_wechat_alarm_config` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint NOT NULL COMMENT '租户ID',
  `customer_id` bigint DEFAULT NULL COMMENT '客户ID（多租户标识）',
  `type` varchar(20) NOT NULL COMMENT '微信类型: enterprise/official',
  `corp_id` varchar(100) DEFAULT NULL COMMENT '企业微信企业ID',
  `agent_id` varchar(50) DEFAULT NULL COMMENT '企业微信应用ID',
  `secret` varchar(100) DEFAULT NULL COMMENT '企业微信应用Secret',
  `appid` varchar(100) DEFAULT NULL COMMENT '微信公众号AppID',
  `appsecret` varchar(100) DEFAULT NULL COMMENT '微信公众号AppSecret',
  `template_id` varchar(100) DEFAULT NULL COMMENT '微信模板ID',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  -- 标准字段
  PRIMARY KEY (`id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_type` (`type`)
);
```

### 2. 消息配置表 (t_message_config)

```sql
CREATE TABLE `t_message_config` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` bigint NOT NULL COMMENT '客户ID（租户ID）',
  `name` varchar(100) NOT NULL COMMENT '配置名称',
  `type` varchar(20) NOT NULL COMMENT '消息类型: sms/email/webhook/internal',
  `endpoint` varchar(500) NOT NULL COMMENT '接收地址',
  `access_key` varchar(200) DEFAULT NULL COMMENT 'Access Key',
  `secret_key` varchar(200) DEFAULT NULL COMMENT 'Secret Key',
  `template_id` varchar(100) DEFAULT NULL COMMENT '模板ID',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `description` text DEFAULT NULL COMMENT '备注描述',
  -- 标准字段
  PRIMARY KEY (`id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_type` (`type`)
);
```

## 🔧 API接口设计

### 微信配置相关接口
```typescript
// 获取微信配置列表
GET /t_wechat_alarm_config/page
// 新增微信配置  
POST /t_wechat_alarm_config/
// 更新微信配置
PUT /t_wechat_alarm_config/
// 删除微信配置
DELETE /t_wechat_alarm_config/
```

### 消息配置相关接口
```typescript
// 获取消息配置列表
GET /t_message_config/page
// 新增消息配置
POST /t_message_config/
// 更新消息配置
PUT /t_message_config/
// 删除消息配置
DELETE /t_message_config/
```

## 💻 前端实现要点

### 1. 三标签页架构
```vue
<NTabs v-model:value="activeTab" type="line" @update:value="handleTabChange">
  <NTabPane name="enterprise" tab="企业微信配置">
    <!-- 企业微信配置表格 -->
  </NTabPane>
  <NTabPane name="official" tab="微信公众号配置">
    <!-- 微信公众号配置表格 -->
  </NTabPane>
  <NTabPane name="message" tab="消息配置">
    <!-- 消息配置表格 -->
  </NTabPane>
</NTabs>
```

### 2. 多表格管理
- 每个标签页都有独立的表格状态管理
- 独立的搜索参数、分页、选中状态
- 独立的CRUD操作和数据刷新

### 3. 动态表单
- 企业微信：企业ID、应用ID、应用Secret
- 微信公众号：AppID、AppSecret
- 消息配置：根据类型显示不同字段

### 4. 多租户过滤
```typescript
const customerId = authStore.userInfo?.customerId;

// API调用时自动包含customer_id过滤
apiParams: {
  customerId: customerId,
  type: 'enterprise'
}
```

## 📊 TypeScript类型定义

```typescript
declare namespace Api.Health {
  // 微信配置
  interface AlertConfigWechat extends Common.CommonRecord {
    tenantId?: number;
    customerId?: number;
    type: 'enterprise' | 'official';
    corpId?: string;
    agentId?: string;
    secret?: string;
    appid?: string;
    appsecret?: string;
    templateId?: string;
    enabled: boolean;
  }

  // 消息配置
  interface MessageConfig extends Common.CommonRecord {
    customerId: number;
    name: string;
    type: 'sms' | 'email' | 'webhook' | 'internal';
    endpoint: string;
    accessKey?: string;
    secretKey?: string;
    templateId?: string;
    enabled: boolean;
    description?: string;
  }
}
```

## 🚀 部署说明

### 1. 数据库迁移
```bash
# 执行数据库迁移脚本
mysql -u root -p < migration_alert_config_multi_tenant.sql
```

### 2. 前端组件
- 已创建完整的前端组件结构
- 所有组件都支持响应式设计
- 具备完整的错误处理和用户反馈

### 3. 权限配置
```typescript
// 需要配置的权限点
't:wechat:alarm:config:add'     // 新增微信配置
't:wechat:alarm:config:update'  // 编辑微信配置  
't:wechat:alarm:config:delete'  // 删除微信配置
't:message:config:add'          // 新增消息配置
't:message:config:update'       // 编辑消息配置
't:message:config:delete'       // 删除消息配置
```

## ✅ 验证清单

- [x] 三标签页正确显示和切换
- [x] 企业微信配置CRUD操作
- [x] 微信公众号配置CRUD操作
- [x] 消息配置CRUD操作
- [x] 多租户数据隔离
- [x] 权限控制
- [x] 响应式布局
- [x] 表单验证
- [x] 错误处理

## 🔄 后续扩展

1. **告警规则关联**：配置可与告警规则进行关联
2. **消息模板管理**：支持自定义消息模板
3. **发送测试功能**：支持配置测试发送
4. **统计报表**：配置使用情况统计
5. **导入导出**：批量配置导入导出功能

## 📝 技术总结

这个实现方案充分体现了现代Web应用的设计理念：

- **模块化架构**：清晰的组件分离和复用
- **类型安全**：完整的TypeScript类型定义
- **多租户支持**：企业级应用的基础要求
- **用户体验**：直观的标签页界面和操作反馈
- **可扩展性**：为后续功能扩展预留接口

通过这个方案，ljwx-admin系统现在具备了完整的告警配置管理能力，支持多种通知渠道和多租户场景。