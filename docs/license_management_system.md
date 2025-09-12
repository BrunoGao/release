# LJWX License 管理系统完整解决方案

## 📋 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [核心功能](#核心功能)
4. [部署指南](#部署指南)
5. [使用说明](#使用说明)
6. [API文档](#api文档)
7. [故障排除](#故障排除)
8. [最佳实践](#最佳实践)

## 系统概述

LJWX License管理系统是一套完整的软件授权管理解决方案，支持多租户架构，提供设备数量限制、并发控制、功能权限管理等核心功能。系统分为三个主要组件：

- **ljwx-boot**: 后端License服务，提供License验证、租户管理、统计监控
- **ljwx-bigscreen**: 大屏系统License集成，实现设备接入控制和并发限制
- **ljwx-admin**: 前端管理界面，提供License配置、监控、导入等功能

### 🎯 核心价值

- **设备限制**: 精确控制接入设备数量，防止超出License范围
- **并发控制**: 实时监控并发请求，确保系统稳定运行
- **多租户支持**: 支持租户级别的License配置和权限控制
- **实时监控**: 提供详细的使用统计和告警机制
- **灵活管理**: 支持License导入、在线配置、批量管理

## 架构设计

### 🏗️ 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ljwx-admin    │    │   ljwx-boot     │    │ ljwx-bigscreen  │
│   前端管理界面     │    │   License服务    │    │   大屏设备接入    │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ 超级管理员   │ │    │ │ License     │ │    │ │ License     │ │
│ │ License管理  │ │◄──►│ │ Manager     │ │◄──►│ │ Manager     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ 租户管理员   │ │    │ │ Customer    │ │    │ │ Device      │ │
│ │ License查看  │ │    │ │ License     │ │    │ │ Monitor     │ │
│ └─────────────┘ │    │ │ Service     │ │    │ └─────────────┘ │
└─────────────────┘    │ └─────────────┘ │    └─────────────────┘
                       │                 │
                       │ ┌─────────────┐ │
                       │ │ License     │ │
                       │ │ Validation  │ │
                       │ │ & Control   │ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

### 📊 数据流图

```
设备请求 → BigScreen License验证 → Boot License API → 数据库验证 → 返回结果
    ↓
设备注册 → 设备计数更新 → Redis缓存 → 实时监控 → 告警检查
    ↓
管理操作 → Admin界面 → Boot管理API → 配置更新 → 状态同步
```

### 🔗 核心组件关系

1. **ljwx-boot (License服务核心)**
   - `LicenseManager`: 核心License管理器
   - `CustomerLicenseService`: 客户License集成服务
   - `LicenseManagementService`: License管理业务服务
   - `LicenseManagementController`: License管理API控制器

2. **ljwx-bigscreen (设备接入控制)**
   - `BigScreenLicenseManager`: BigScreen License管理器
   - `license_required`: License验证装饰器
   - API集成: 设备数量和并发限制

3. **ljwx-admin (管理界面)**
   - 系统级License管理: `/system/license/`
   - 租户级License管理: `/tenant/license/`
   - License API服务: `/service/api/system/license.ts`

## 核心功能

### 🔐 License验证机制

#### 1. 多层验证架构

```python
# 验证流程
def license_validation_flow(device_sn, customer_id):
    # 第一层：系统级License检查
    if not system_license_valid():
        return False, "系统License无效"
    
    # 第二层：租户License配置检查
    if not customer_license_enabled(customer_id):
        return False, "租户License未启用"
    
    # 第三层：设备数量限制检查
    if not check_device_limit(device_sn, customer_id):
        return False, "设备数量超出限制"
    
    # 第四层：并发限制检查
    if not check_concurrent_limit(customer_id):
        return False, "并发请求超出限制"
    
    return True, "验证通过"
```

#### 2. 设备接入控制

- **设备注册**: 自动注册新设备，检查数量限制
- **活跃监控**: 实时监控设备活跃状态，自动清理离线设备
- **一致性保证**: 基于设备SN的一致性哈希，确保同一设备始终走相同路径

#### 3. 并发控制机制

- **实时计数**: 基于Redis的实时并发请求计数
- **自动释放**: 请求完成后自动释放并发计数
- **租户隔离**: 按租户分别统计并发数量

### 📊 监控和统计

#### 1. 实时监控指标

- License有效性状态
- 设备使用情况（当前/最大）
- 并发请求数量（当前/最大）
- 租户启用统计
- 功能使用统计

#### 2. 告警机制

- License即将过期告警（30天、7天）
- 设备使用率超限告警（90%）
- 并发请求超限告警
- 系统异常告警

#### 3. 历史数据跟踪

- License操作历史
- 设备连接历史
- 使用趋势分析
- 异常事件记录

### 👥 多租户管理

#### 1. 租户级别控制

- 独立的License启用/禁用配置
- 租户级别的使用统计
- 租户管理员自助License导入
- 租户级别的监控告警

#### 2. 权限分级

- **超级管理员**: 全局License管理、所有租户管理
- **租户管理员**: 仅自己租户的License查看和导入
- **普通用户**: License状态查看

## 部署指南

### 🚀 环境要求

- **Java**: JDK 17+
- **Python**: Python 3.8+
- **数据库**: MySQL 8.0+
- **缓存**: Redis 6.0+
- **前端**: Node.js 16+

### 📦 部署步骤

#### 1. ljwx-boot 部署

```bash
# 1. 添加License相关依赖（已包含在现有项目中）
# 2. 配置数据库连接
spring.datasource.url=jdbc:mysql://localhost:3306/ljwx_db
spring.datasource.username=root
spring.datasource.password=your_password

# 3. 配置Redis连接
spring.redis.host=localhost
spring.redis.port=6379
spring.redis.password=your_redis_password

# 4. License配置
ljwx.license.file-path=./license/ljwx.lic
ljwx.license.check-interval=300

# 5. 启动服务
cd ljwx-boot
./run-local.sh start
```

#### 2. ljwx-bigscreen 部署

```bash
# 1. 确保依赖已安装
cd ljwx-bigscreen/bigscreen/bigScreen
pip install requests

# 2. 配置Boot API地址
# 在 license_manager.py 中配置
boot_api_base_url = "http://localhost:8080/api"

# 3. 启动BigScreen服务
python run_bigscreen.py
```

#### 3. ljwx-admin 部署

```bash
# 1. 安装依赖
cd ljwx-admin
npm install

# 2. 配置API地址
# 在 .env 中配置
VITE_API_BASE_URL=http://localhost:8080

# 3. 启动开发服务器
npm run dev

# 4. 生产构建
npm run build
```

### 🔧 配置说明

#### 1. License文件配置

```yaml
# ljwx.lic 示例结构
licenseId: "LIC-20241201-001"
customerName: "示例客户"
licenseType: "enterprise"
maxDevices: 100
maxUsers: 500
features:
  - "bigscreen_access"
  - "user_management"
  - "device_monitoring"
  - "health_analytics"
startDate: "2024-01-01T00:00:00"
endDate: "2025-01-01T00:00:00"
```

#### 2. 数据库初始化

```sql
-- 租户配置表
ALTER TABLE t_customer_config 
ADD COLUMN is_support_license TINYINT(1) DEFAULT 0 COMMENT '是否支持License功能';

-- License使用记录表（可选）
CREATE TABLE t_license_usage_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT,
    operation VARCHAR(50),
    description TEXT,
    user_id BIGINT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. Redis配置

```redis
# Redis配置建议
maxmemory 2gb
maxmemory-policy allkeys-lru

# License相关键值设置
set ljwx:license:global:enabled true
```

## 使用说明

### 👑 超级管理员操作

#### 1. License导入

1. 登录ljwx-admin管理界面
2. 导航到 `系统管理 > License管理`
3. 点击 `导入License` 按钮
4. 选择.lic格式的License文件
5. 确认导入，系统自动验证并生效

#### 2. 全局License控制

```javascript
// 全局启用License功能
PUT /api/license/management/toggle/true

// 全局禁用License功能
PUT /api/license/management/toggle/false
```

#### 3. 租户License管理

1. 在租户列表中选择目标租户
2. 点击 `启用/禁用` 按钮切换租户License状态
3. 点击 `查看状态` 查看详细License信息

#### 4. 监控和统计

- **实时状态**: 查看License有效性、设备使用情况、并发状态
- **使用统计**: 查看历史使用趋势、功能使用统计
- **告警管理**: 监控License过期、使用率告警

### 🏢 租户管理员操作

#### 1. 查看License状态

1. 登录ljwx-admin管理界面
2. 导航到 `我的License`
3. 查看License详细信息、使用情况、剩余时间

#### 2. 导入License

1. 在 `我的License` 页面点击 `导入License`
2. 上传新的License文件
3. 系统自动验证并更新配置

#### 3. 监控设备使用

- 查看当前在线设备列表
- 监控设备使用率和趋势
- 接收使用率告警

### 🖥️ BigScreen设备接入

#### 1. 自动License验证

```python
# 设备数据上传时自动验证
@app.route("/upload_health_data", methods=['POST'])
def handle_health_data():
    # License验证已集成到数据上传流程
    # 自动检查设备数量和并发限制
    pass
```

#### 2. License状态查询

```bash
# 查询BigScreen License状态
curl http://localhost:5225/api/license/status

# 查询License仪表板数据
curl http://localhost:5225/api/license/dashboard
```

#### 3. 设备权限检查

```python
# 检查特定设备的License权限
from bigScreen.license_manager import check_device_license

result = check_device_license("DEVICE_001", customer_id=1)
if result['allowed']:
    print("设备接入权限正常")
else:
    print(f"设备接入被拒绝: {result['reason']}")
```

## API文档

### 🔌 ljwx-boot License API

#### 1. 系统级License管理

```http
# 获取License状态
GET /api/license/management/status
Response: {
    "success": true,
    "data": {
        "licenseEnabled": true,
        "licenseValid": true,
        "globalEnabled": true,
        "licenseInfo": {...},
        "remainingDays": 365
    }
}

# 导入License
POST /api/license/management/import
Content-Type: multipart/form-data
Body: file=@license.lic

# 全局启用/禁用License
POST /api/license/management/toggle/{enabled}
```

#### 2. 租户License管理

```http
# 获取租户License列表
GET /api/license/management/tenant/list?pageNum=1&pageSize=10

# 租户License启用/禁用
POST /api/license/management/tenant/{customerId}/toggle/{enabled}

# 获取租户License状态
GET /api/license/management/tenant/{customerId}/status
```

#### 3. License统计和监控

```http
# 获取License使用统计
GET /api/license/management/statistics

# 获取License使用历史
GET /api/license/management/usage/history

# 重新验证License
POST /api/license/management/revalidate
```

### 🖥️ ljwx-bigscreen License API

#### 1. License状态查询

```http
# 获取License状态
GET /api/license/status
Response: {
    "success": true,
    "data": {
        "license_valid": true,
        "device_limits": {
            "max_devices": 100,
            "current_devices": 15,
            "active_devices": ["DEV001", "DEV002"]
        },
        "concurrent_limits": {
            "max_concurrent": 500,
            "current_concurrent": 23
        }
    }
}

# 获取License仪表板数据
GET /api/license/dashboard

# 检查设备License权限
POST /api/license/device/check
Body: {
    "device_sn": "DEVICE_001",
    "customer_id": 1
}
```

### 🎨 ljwx-admin License API

#### 1. TypeScript类型定义

```typescript
// License信息类型
interface LicenseInfo {
    licenseId: string
    customerName: string
    licenseType: string
    maxDevices: number
    maxUsers: number
    features: string[]
    startDate: string
    endDate: string
}

// 租户License状态类型
interface TenantLicenseStatus {
    customerId: number
    effectiveLicenseEnabled: boolean
    licenseInfo?: LicenseInfo
    remainingDays?: number
}
```

#### 2. API服务调用

```typescript
import { getLicenseStatus, importLicense } from '@/service/api/system/license'

// 获取License状态
const status = await getLicenseStatus()

// 导入License文件
const result = await importLicense(file)
```

## 故障排除

### 🚨 常见问题

#### 1. License验证失败

**症状**: BigScreen设备无法接入，返回License验证失败
**原因**: 
- License文件无效或已过期
- Boot服务无法连接
- License功能被全局禁用

**解决方案**:
```bash
# 1. 检查License文件有效性
curl http://localhost:8080/api/license/management/status

# 2. 检查Boot服务连接
curl http://localhost:8080/health

# 3. 检查License全局状态
curl http://localhost:8080/api/license/management/status | grep globalEnabled

# 4. 重新验证License
curl -X POST http://localhost:8080/api/license/management/revalidate
```

#### 2. 设备数量超限

**症状**: 新设备无法接入，提示设备数量超出限制
**原因**:
- 达到License设备数量上限
- 离线设备未及时清理

**解决方案**:
```python
# 1. 检查当前设备使用情况
from bigScreen.license_manager import get_license_manager
manager = get_license_manager()
status = manager.get_license_status()
print(f"设备使用情况: {status['device_limits']}")

# 2. 手动清理离线设备
manager.cleanup_expired_devices()

# 3. 检查License设备限制
print(f"设备限制: {manager.get_device_limits()}")
```

#### 3. 并发请求超限

**症状**: 健康数据上传失败，提示并发超限
**原因**:
- 瞬时并发请求过多
- 并发计数未正确释放

**解决方案**:
```python
# 1. 检查当前并发情况
status = manager.get_license_status()
print(f"并发情况: {status['concurrent_limits']}")

# 2. 重置并发计数（紧急情况）
with manager.request_counter_lock:
    manager.concurrent_requests.clear()

# 3. 调整并发限制（临时）
max_devices, max_concurrent = manager.get_device_limits()
# 可以在代码中临时调整限制
```

#### 4. 前端界面异常

**症状**: License管理界面加载失败或显示异常
**原因**:
- API接口连接失败
- 权限不足
- 数据格式异常

**解决方案**:
```bash
# 1. 检查API连接
curl http://localhost:8080/api/license/management/status

# 2. 检查用户权限
# 确保用户具有相应的License管理权限

# 3. 检查浏览器控制台错误
# 打开浏览器开发者工具，查看错误信息

# 4. 清除浏览器缓存
# 清除缓存后重新加载页面
```

### 🔍 日志分析

#### 1. ljwx-boot 日志

```bash
# License相关日志位置
tail -f ljwx-boot/logs/license.log

# 关键日志示例
2024-01-01 10:00:00 [INFO] License验证通过, 客户: 客户A
2024-01-01 10:00:01 [WARN] 设备数量接近限制, 当前: 95, 最大: 100
2024-01-01 10:00:02 [ERROR] License验证失败: License已过期
```

#### 2. ljwx-bigscreen 日志

```bash
# BigScreen License日志
tail -f ljwx-bigscreen/bigscreen/logs/bigscreen.log | grep License

# 关键日志示例
2024-01-01 10:00:00 [INFO] ✅ License验证通过: DEVICE_001
2024-01-01 10:00:01 [WARN] ❌ License验证失败: 设备数量超出限制
2024-01-01 10:00:02 [INFO] 🔐 License管理器初始化完成
```

### 📊 监控告警配置

#### 1. 设置监控脚本

```bash
#!/bin/bash
# license_monitor.sh
# License状态监控脚本

API_BASE="http://localhost:8080/api"
WEBHOOK_URL="your_alert_webhook_url"

# 检查License状态
status=$(curl -s "$API_BASE/license/management/status")
license_valid=$(echo $status | jq -r '.data.licenseValid')
remaining_days=$(echo $status | jq -r '.data.remainingDays')

# License过期告警
if [ "$remaining_days" -lt 7 ]; then
    curl -X POST $WEBHOOK_URL -d "{\"text\": \"License即将过期，剩余${remaining_days}天\"}"
fi

# 设备使用率告警
device_stats=$(curl -s "$API_BASE/license/management/statistics")
usage_rate=$(echo $device_stats | jq -r '.data.deviceUsageRate')

if [ "$usage_rate" -gt 90 ]; then
    curl -X POST $WEBHOOK_URL -d "{\"text\": \"设备使用率过高：${usage_rate}%\"}"
fi
```

#### 2. 定时任务配置

```bash
# 添加到crontab
crontab -e

# 每小时检查一次License状态
0 * * * * /path/to/license_monitor.sh

# 每天检查一次过期情况
0 9 * * * /path/to/license_expiry_check.sh
```

## 最佳实践

### 🎯 License管理最佳实践

#### 1. License文件管理

- **版本控制**: 为License文件建立版本控制，记录每次更新
- **备份策略**: 定期备份License文件和配置，确保快速恢复
- **权限控制**: 严格控制License文件的访问权限
- **更新流程**: 建立标准的License更新流程和审批机制

#### 2. 监控和告警

- **提前告警**: 设置30天、7天的过期提醒
- **使用率监控**: 当设备使用率超过80%时发出警告
- **异常检测**: 监控License验证失败率，及时发现问题
- **定期检查**: 建立定期的License状态检查机制

#### 3. 租户管理

- **分级管理**: 建立清晰的权限分级，避免权限混乱
- **自助服务**: 为租户管理员提供自助License导入功能
- **使用统计**: 定期向租户提供License使用报告
- **容量规划**: 根据使用趋势进行License容量规划

#### 4. 性能优化

- **缓存策略**: 合理使用Redis缓存，减少数据库压力
- **批量处理**: 对大量设备的License检查使用批量处理
- **异步处理**: 非关键License操作使用异步处理
- **连接池**: 配置合适的数据库连接池大小

### 🔒 安全建议

#### 1. License文件安全

```bash
# 设置License文件权限
chmod 600 ./license/ljwx.lic
chown ljwx:ljwx ./license/ljwx.lic

# 加密存储敏感信息
# 使用环境变量存储License密钥
export LICENSE_KEY="your_secret_key"
```

#### 2. API安全

- **认证授权**: 所有License管理API都需要适当的认证授权
- **访问控制**: 基于角色的访问控制，限制敏感操作权限
- **审计日志**: 记录所有License相关操作的审计日志
- **加密传输**: 使用HTTPS加密所有API通信

#### 3. 数据保护

- **数据加密**: 敏感License信息进行加密存储
- **备份加密**: License备份文件进行加密保护
- **访问日志**: 记录所有License数据访问日志
- **定期清理**: 定期清理过期的License使用记录

### 📈 扩展性考虑

#### 1. 水平扩展

- **无状态设计**: License验证逻辑设计为无状态，支持多实例部署
- **缓存共享**: 使用Redis集群实现多实例间的缓存共享
- **负载均衡**: 配置适当的负载均衡策略

#### 2. 功能扩展

- **插件机制**: 设计License功能的插件机制，支持定制化需求
- **多级License**: 支持企业版、专业版、标准版等多级License
- **动态功能**: 支持运行时动态启用/禁用功能模块

#### 3. 集成扩展

- **第三方集成**: 支持与外部License服务的集成
- **API开放**: 提供开放API供第三方系统集成
- **标准协议**: 遵循行业标准的License管理协议

### 📋 运维检查清单

#### 日常检查

- [ ] License有效性状态
- [ ] 设备使用率（建议<80%）
- [ ] 并发请求状况
- [ ] 系统告警信息
- [ ] API响应时间

#### 每周检查

- [ ] License剩余时间
- [ ] 租户License配置
- [ ] 使用趋势分析
- [ ] 异常事件回顾
- [ ] 性能指标评估

#### 每月检查

- [ ] License使用报告
- [ ] 容量规划评估
- [ ] 安全漏洞检查
- [ ] 备份恢复测试
- [ ] 流程优化建议

## 联系支持

如果在使用过程中遇到问题，请提供以下信息：

1. **错误信息**: 完整的错误日志和堆栈信息
2. **系统环境**: 操作系统、Java版本、Python版本等
3. **License信息**: License类型、过期时间、功能列表
4. **操作步骤**: 详细的问题复现步骤
5. **相关配置**: 相关的配置文件和参数设置

---

**版本**: v1.0.0  
**更新时间**: 2024年12月  
**文档维护**: LJWX技术团队

> 💡 **提示**: 本文档会随着系统更新持续完善，建议定期查看最新版本。