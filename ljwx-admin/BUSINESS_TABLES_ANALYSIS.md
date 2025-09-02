# 业务表多租户 customer_id 字段分析报告

## 概述

本报告基于对 ljwx-admin 系统数据库的深入分析，为缺失 customer_id 字段的核心业务表提供完整的多租户迁移方案。系统已具备成熟的多租户架构基础，本次升级将实现业务数据的完整租户隔离。

## 当前多租户架构分析

### 已实现的多租户表
- ✅ `sys_user` - 用户表（customer_id 已实现）
- ✅ `sys_org_units` - 组织表（customer_id 已实现） 
- ✅ `sys_role` - 角色表（customer_id 已实现）
- ✅ `sys_position` - 岗位表（customer_id 已实现）
- ✅ `sys_user_org` - 用户组织关联表（customer_id 已实现）
- ✅ `t_alert_rule` - 告警规则表（customer_id 已实现）
- ✅ `t_wechat_alarm_config` - 微信告警配置表（customer_id 已实现）

### 成熟的索引设计模式
系统已建立完善的多租户索引策略：
- `idx_[table]_customer_id` - 基础租户过滤索引
- `idx_[table]_customer_[field]` - 租户+业务字段复合索引  
- `idx_[table]_customer_status` - 租户+状态复合索引

## 待迁移的核心业务表详细分析

### Priority 1: 核心业务表

#### 1. t_user_health_data (用户健康数据表)

**当前结构分析：**
```sql
CREATE TABLE t_user_health_data (
  id int NOT NULL AUTO_INCREMENT,
  phone_number varchar(20),
  heart_rate int, pressure_high int, pressure_low int,
  blood_oxygen int, stress int, temperature double(5,2),
  step int, timestamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_name varchar(255) NOT NULL DEFAULT 'heguang',
  latitude decimal(10,6), longitude decimal(10,6), altitude double,
  device_sn varchar(255) NOT NULL,
  distance double, calorie double,
  user_id bigint, org_id bigint,
  -- 缺少 customer_id 字段
);
```

**关系分析：**
- 通过 `user_id` 关联到 `sys_user.id`（已有 customer_id）
- 通过 `device_sn` 关联到设备信息
- 通过 `org_id` 关联到组织结构（已有 customer_id）

**customer_id 确定策略：**
1. **主要策略**：从 `user_id` → `sys_user.customer_id` 继承租户ID
2. **备选策略**：从 `org_id` → `sys_org_units.customer_id` 继承（当user_id为空时）

**推荐索引：**
```sql
-- 按租户+设备+时间查询（设备历史数据）
CREATE INDEX idx_health_customer_device_time ON t_user_health_data(customer_id, device_sn, timestamp);
-- 按租户+用户+时间查询（个人健康报告）  
CREATE INDEX idx_health_customer_user_time ON t_user_health_data(customer_id, user_id, timestamp);
-- 按租户+组织+时间查询（组织健康统计）
CREATE INDEX idx_health_customer_org_time ON t_user_health_data(customer_id, org_id, timestamp);
```

**业务影响评估：**
- 🔥 **高影响**：健康数据是系统核心，必须严格按租户隔离
- 📊 **查询优化**：多租户索引将显著提升健康报告生成速度
- 🔒 **数据安全**：防止跨租户健康隐私数据泄露

---

#### 2. t_device_info (设备信息表)

**当前结构分析：**
```sql
CREATE TABLE t_device_info (
  id int NOT NULL AUTO_INCREMENT,
  system_software_version varchar(255) NOT NULL,
  wifi_address varchar(255), bluetooth_address varchar(255),
  ip_address varchar(255), serial_number varchar(255),
  device_name varchar(255), imei varchar(255),
  battery_level int, model varchar(50),
  status enum('INACTIVE','ACTIVE'),
  -- 缺少 customer_id, user_id, org_id 字段
);
```

**数据关系复杂性：**
- 设备信息表当前缺少直接的用户/组织关联
- 需要通过 `t_device_user` 表的绑定关系确定租户归属
- 一个设备可能在不同时期绑定给不同租户的用户

**customer_id 确定策略：**
1. **当前绑定策略**：从当前有效绑定 `t_device_user` → `sys_user.customer_id`
2. **历史绑定策略**：如果没有当前绑定，取最后一次绑定记录的租户
3. **默认策略**：未绑定设备设置为 customer_id = 0（全局设备池）

**建议增加字段：**
```sql
ALTER TABLE t_device_info 
ADD COLUMN customer_id BIGINT NOT NULL DEFAULT '0' COMMENT '租户ID，继承自当前绑定用户',
ADD COLUMN user_id BIGINT DEFAULT NULL COMMENT '当前绑定用户ID',  
ADD COLUMN org_id BIGINT DEFAULT NULL COMMENT '当前绑定组织ID';
```

**推荐索引：**
```sql
-- 租户设备管理核心索引
CREATE INDEX idx_device_customer_serial ON t_device_info(customer_id, serial_number);
CREATE INDEX idx_device_customer_user ON t_device_info(customer_id, user_id);
CREATE INDEX idx_device_customer_status ON t_device_info(customer_id, status);
```

**业务影响评估：**
- 🔥 **高影响**：设备是物联网系统的核心资源，必须严格管理归属
- 📱 **设备管理**：支持按租户查看和管理设备资产
- 🔄 **绑定历史**：保留设备在不同租户间流转的历史记录

---

#### 3. t_device_message & t_device_message_detail (设备消息表)

**当前结构分析：**
```sql
-- 主消息表
CREATE TABLE t_device_message (
  id bigint NOT NULL AUTO_INCREMENT,
  user_id bigint COMMENT '用户ID',
  device_sn varchar(255),
  message text NOT NULL,
  message_type varchar(50) NOT NULL,
  message_status varchar(50) NOT NULL DEFAULT 'pending',
  -- 缺少 customer_id 字段
);

-- 消息详情表  
CREATE TABLE t_device_message_detail (
  id bigint NOT NULL AUTO_INCREMENT,
  message_id varchar(255) NOT NULL,
  device_sn varchar(255) NOT NULL, 
  message text NOT NULL,
  -- 缺少 customer_id 字段
);
```

**关系分析：**
- 主消息表通过 `user_id` 直接关联用户租户
- 详情表通过 `message_id` 关联到主消息表

**customer_id 确定策略：**
1. **t_device_message**：从 `user_id` → `sys_user.customer_id` 直接继承
2. **t_device_message_detail**：从关联的 `t_device_message.customer_id` 继承

**推荐索引：**
```sql
-- 设备消息时序查询
CREATE INDEX idx_message_customer_device_time ON t_device_message(customer_id, device_sn, create_time);
-- 用户消息状态查询
CREATE INDEX idx_message_customer_user_status ON t_device_message(customer_id, user_id, message_status);
-- 消息详情快速定位
CREATE INDEX idx_message_detail_customer_device ON t_device_message_detail(customer_id, device_sn);
```

**业务影响评估：**
- 🔥 **高影响**：消息系统承载设备通讯，需要严格的租户隔离
- 💬 **通讯安全**：防止跨租户消息泄露和误发
- 📈 **性能优化**：按租户索引将显著提升消息查询性能

---

#### 4. t_alert_info & t_alert_action_log (告警信息及操作日志)

**当前结构分析：**
```sql
-- 告警信息表（已有 tenant_id，需重命名为 customer_id）
CREATE TABLE t_alert_info (
  id bigint unsigned NOT NULL AUTO_INCREMENT,
  rule_id bigint NOT NULL,
  device_sn varchar(20) NOT NULL,
  user_id bigint COMMENT '用户ID',
  org_id bigint COMMENT '组织ID', 
  tenant_id bigint DEFAULT '1' COMMENT '租户ID', -- 需重命名
);

-- 告警操作日志表  
CREATE TABLE t_alert_action_log (
  log_id bigint unsigned NOT NULL AUTO_INCREMENT,
  alert_id bigint unsigned NOT NULL,
  action_user_id bigint DEFAULT NULL,
  -- 缺少 customer_id 字段
);
```

**特殊情况：**
- `t_alert_info` 已有 `tenant_id` 字段，但名称不统一，需重命名为 `customer_id`
- `t_alert_action_log` 需要从关联的告警记录继承租户信息

**customer_id 确定策略：**
1. **t_alert_info**：重命名现有 `tenant_id` 为 `customer_id`，确保数据一致性
2. **t_alert_action_log**：从 `alert_id` → `t_alert_info.customer_id` 继承

**索引更新：**
```sql
-- 删除旧索引，创建新索引
DROP INDEX idx_alert_info_tenant_status ON t_alert_info;
CREATE INDEX idx_alert_info_customer_status ON t_alert_info(customer_id, alert_status);
CREATE INDEX idx_alert_log_customer_alert ON t_alert_action_log(customer_id, alert_id);
```

**业务影响评估：**
- 🔥 **高影响**：告警系统是安全监控核心，租户隔离至关重要
- 🚨 **安全告警**：防止跨租户告警信息泄露
- 📋 **操作审计**：操作日志按租户隔离，便于审计追踪

---

#### 5. t_device_bind_request & t_device_user (设备绑定管理)

**当前结构分析：**
```sql
-- 设备绑定申请表
CREATE TABLE t_device_bind_request (
  id bigint NOT NULL AUTO_INCREMENT,
  device_sn varchar(100) NOT NULL,
  user_id bigint NOT NULL COMMENT '申请用户ID',
  org_id bigint NOT NULL COMMENT '申请组织ID',
  -- 缺少 customer_id 字段
);

-- 设备用户关联表
CREATE TABLE t_device_user (
  id bigint unsigned NOT NULL AUTO_INCREMENT,
  device_sn varchar(200) NOT NULL,
  user_id bigint NOT NULL,
  status enum('BIND','UNBIND') DEFAULT 'BIND',
  -- 缺少 customer_id 字段  
);
```

**关系分析：**
- 两表都直接关联用户，可从 `user_id` 继承租户信息
- 设备绑定流程：申请 → 审批 → 绑定，全流程需要租户一致性

**customer_id 确定策略：**
- 从 `user_id` → `sys_user.customer_id` 直接继承，确保设备绑定在正确租户范围内

**推荐索引：**
```sql
-- 设备绑定申请管理
CREATE INDEX idx_bind_request_customer_device ON t_device_bind_request(customer_id, device_sn);
CREATE INDEX idx_bind_request_customer_user ON t_device_bind_request(customer_id, user_id);

-- 设备用户关联查询
CREATE INDEX idx_device_user_customer_device ON t_device_user(customer_id, device_sn);  
CREATE INDEX idx_device_user_customer_user ON t_device_user(customer_id, user_id);
```

**业务影响评估：**
- 🔥 **高影响**：设备绑定是权限管理基础，必须按租户严格隔离
- 🔐 **权限控制**：确保用户只能申请和绑定本租户设备
- 📊 **资产管理**：按租户统计设备绑定情况和使用率

---

#### 6. 健康分析表组 (t_health_baseline, t_org_health_baseline, t_health_score, t_org_health_score)

**当前结构分析：**
```sql
-- 个人健康基线表
CREATE TABLE t_health_baseline (
  id bigint NOT NULL AUTO_INCREMENT,
  device_sn varchar(50) NOT NULL,
  user_id bigint DEFAULT '0',
  org_id varchar(20) DEFAULT '1',
  feature_name varchar(20) NOT NULL,
  baseline_date date NOT NULL,
  -- 缺少 customer_id 字段
);

-- 组织健康基线表
CREATE TABLE t_org_health_baseline (
  id bigint NOT NULL AUTO_INCREMENT,  
  org_id varchar(20) NOT NULL,
  feature_name varchar(20) NOT NULL,
  baseline_date date NOT NULL,
  -- 缺少 customer_id 字段
);

-- 健康评分表（个人和组织，结构类似）
```

**数据关系复杂性：**
- **个人表**：通过 `device_sn` → `t_device_user` → `sys_user` 间接获取租户
- **组织表**：通过 `org_id` → `sys_org_units.customer_id` 直接获取租户
- 数据链路：设备 → 用户 → 租户，需要多表关联确定归属

**customer_id 确定策略：**
1. **个人表**：`device_sn` → `t_device_user`(当前绑定) → `sys_user.customer_id`
2. **组织表**：`org_id` → `sys_org_units.customer_id` 直接映射

**推荐索引：**
```sql
-- 个人健康分析查询优化
CREATE INDEX idx_health_baseline_customer_device_feature ON t_health_baseline(customer_id, device_sn, feature_name, baseline_date);
CREATE INDEX idx_health_score_customer_device_date ON t_health_score(customer_id, device_sn, score_date);

-- 组织健康分析查询优化  
CREATE INDEX idx_org_baseline_customer_org_feature ON t_org_health_baseline(customer_id, org_id, feature_name, baseline_date);
CREATE INDEX idx_org_score_customer_org_date ON t_org_health_score(customer_id, org_id, score_date);
```

**业务影响评估：**
- 🔥 **高影响**：健康分析是系统核心价值，数据准确性和安全性至关重要
- 📊 **分析报告**：按租户生成健康基线和评分报告
- 🏥 **医疗合规**：健康数据严格按租户隔离，符合医疗数据保护要求

---

## 数据迁移策略

### 迁移原则
1. **数据完整性**：确保所有现有数据正确分配到对应租户
2. **关系一致性**：维护表间关联关系的租户一致性  
3. **性能优化**：创建适当索引，提升多租户查询性能
4. **回滚安全**：提供完整的备份和回滚方案

### 迁移优先级
1. **Phase 1**：基础关联表（t_device_user, t_device_bind_request）
2. **Phase 2**：核心业务表（t_user_health_data, t_alert_info）  
3. **Phase 3**：分析统计表（健康基线和评分表组）
4. **Phase 4**：辅助功能表（消息、设备信息等）

### 数据验证检查点
1. **租户分布统计**：验证数据按租户正确分布
2. **关系一致性**：检查关联表间的租户ID一致性
3. **业务逻辑验证**：确保业务查询结果与迁移前一致
4. **性能基准测试**：对比迁移前后的查询性能

## 后端服务影响分析

### Java 实体类更新需求
基于现有的示例代码结构，需要更新的实体类包括：
```java
// 需要添加 customer_id 字段的实体类
- UserHealthDataEntity.java
- DeviceInfoEntity.java  
- DeviceMessageEntity.java
- AlertInfoEntity.java (重命名 tenantId 为 customerId)
- HealthBaselineEntity.java
// ... 其他相关实体类
```

### API 接口影响
1. **查询接口**：所有查询需要自动添加 `customer_id` 条件
2. **新增接口**：创建数据时自动设置当前用户的 `customer_id`  
3. **权限控制**：确保用户只能操作本租户数据

### Python 服务影响  
根据现有架构，Python 服务（ljwx-bigscreen）需要：
1. **模型更新**：SQLAlchemy 模型添加 `customer_id` 字段
2. **查询修改**：所有数据库查询自动添加租户过滤
3. **上下文管理**：实现租户上下文自动注入

## 性能优化建议

### 索引策略
1. **复合索引优先**：`(customer_id, business_field)` 组合索引
2. **查询覆盖**：常用查询字段组合建立覆盖索引
3. **分区考虑**：大表可按 `customer_id` 进行分区优化

### 查询优化
1. **强制租户过滤**：所有业务查询必须包含 `customer_id` 条件
2. **索引提示**：复杂查询使用索引提示确保最优执行计划
3. **查询重写**：将跨表关联查询改写为租户范围内的高效查询

### 监控建议
1. **慢查询监控**：重点监控多租户查询的执行计划
2. **索引使用率**：定期检查新建索引的使用情况
3. **数据分布**：监控各租户的数据量分布，及时优化

## 风险评估与缓解

### 主要风险
1. **数据迁移风险**：复杂关联可能导致数据分配错误
2. **性能风险**：增加 `customer_id` 字段可能影响现有查询性能
3. **业务兼容性风险**：现有API和业务逻辑需要适配

### 缓解措施  
1. **充分测试**：在测试环境完整验证迁移脚本
2. **分步实施**：按优先级分批迁移，降低单次变更风险
3. **监控告警**：实时监控迁移过程和系统性能指标
4. **快速回滚**：准备完整的数据恢复和回滚预案

## 总结建议

1. **立即执行**：核心业务表的多租户改造刻不容缓，建议优先处理 Priority 1 表
2. **统一标准**：严格按照现有的 `customer_id` 命名和索引规范执行
3. **性能优先**：重点关注健康数据和告警数据的查询性能优化
4. **安全第一**：确保健康隐私数据和告警信息的严格租户隔离

通过本次迁移，系统将实现完整的多租户数据隔离，为企业级应用部署奠定坚实基础。

---

**迁移脚本位置**：`/business-tables-customer-id-migration.sql`  
**执行建议**：在生产环境执行前，请在测试环境完整验证所有业务功能