# 客户Logo管理API文档

## 概述

本文档描述了LJWX系统中客户Logo管理的API接口，支持多租户环境下每个客户的个性化Logo设置。

## 基础信息

- **前端调用**: `http://localhost:3333/customer/logo` 
- **管理端调用**: `http://localhost:3333/t_customer_config/logo`
- **认证方式**: Bearer Token（通过Sa-Token）
- **支持格式**: PNG, JPG, JPEG, SVG, WEBP
- **文件大小限制**: 2MB

## API接口列表

> **说明**: 每个API都有前端调用版本和管理端调用版本，功能完全相同，仅路径前缀不同

### 1. 上传客户Logo

#### 前端版本

**接口描述**: 上传并设置指定客户的自定义Logo

```http
POST /customer/logo/upload
Content-Type: multipart/form-data
```

**请求参数**:
- `file` (FormData) - Logo文件，必需
- `customerId` (FormData) - 客户ID，必需

**请求示例**:
```bash
curl -X POST "http://localhost:3333/customer/logo/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/logo.png" \
  -F "customerId=1"
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Logo上传成功",
  "data": {
    "logoUrl": "/uploads/logos/customer_1/logo_20250128213000_a1b2c3d4.png",
    "fileName": "company-logo.png",
    "uploadTime": "2025-01-28T21:30:00",
    "customerId": 1
  },
  "timestamp": 1640995200000
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "客户不存在: 999",
  "data": null,
  "timestamp": 1640995200000
}
```

#### 管理端版本

```http
POST /t_customer_config/logo/upload
Content-Type: multipart/form-data
```

**权限要求**: `t:customer:config:logo:upload`

**请求示例**:
```bash
curl -X POST "http://localhost:3333/t_customer_config/logo/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/logo.png" \
  -F "customerId=1"
```

### 2. 获取客户Logo

#### 前端版本

**接口描述**: 获取指定客户的Logo文件（如果没有自定义Logo则返回默认Logo）

```http
GET /customer/logo/{customerId}
```

**路径参数**:
- `customerId` - 客户ID，必需

**请求示例**:
```bash
curl -X GET "http://localhost:3333/customer/logo/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应**: 直接返回图片文件，Content-Type为相应的图片类型

**响应头**:
- `Content-Type`: `image/png` | `image/jpeg` | `image/svg+xml`
- `Cache-Control`: `max-age=86400`

#### 管理端版本

```http
GET /t_customer_config/logo/{customerId}
```

**请求示例**:
```bash
curl -X GET "http://localhost:3333/t_customer_config/logo/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应**: 直接返回图片文件

**响应头**:
- `Content-Type`: `image/png` | `image/jpeg` | `image/svg+xml`
- `Cache-Control`: `max-age=3600` (管理端缓存1小时)

### 3. 删除客户Logo

#### 前端版本

**接口描述**: 删除指定客户的自定义Logo，恢复使用默认Logo

```http
DELETE /customer/logo/{customerId}
```

**路径参数**:
- `customerId` - 客户ID，必需

**请求示例**:
```bash
curl -X DELETE "http://localhost:3333/customer/logo/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Logo删除成功，已恢复默认logo",
  "data": null,
  "timestamp": 1640995200000
}
```

#### 管理端版本

```http
DELETE /t_customer_config/logo/{customerId}
```

**权限要求**: `t:customer:config:logo:delete`

**请求示例**:
```bash
curl -X DELETE "http://localhost:3333/t_customer_config/logo/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 获取客户Logo信息

#### 前端版本

**接口描述**: 获取指定客户的Logo相关详细信息

```http
GET /customer/logo/info/{customerId}
```

**路径参数**:
- `customerId` - 客户ID，必需

**请求示例**:
```bash
curl -X GET "http://localhost:3333/customer/logo/info/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "customerId": 1,
    "customerName": "测试客户",
    "hasCustomLogo": true,
    "logoUrl": "/uploads/logos/customer_1/logo_20250128213000_a1b2c3d4.png",
    "logoFileName": "company-logo.png",
    "logoUploadTime": "2025-01-28T21:30:00",
    "defaultLogoUrl": "/customer/logo/1"
  },
  "timestamp": 1640995200000
}
```

#### 管理端版本

```http
GET /t_customer_config/logo/info/{customerId}
```

**权限要求**: `t:customer:config:logo:info`

**请求示例**:
```bash
curl -X GET "http://localhost:3333/t_customer_config/logo/info/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "customerId": 1,
    "customerName": "测试客户",
    "hasCustomLogo": true,
    "logoUrl": "/uploads/logos/customer_1/logo_20250128213000_a1b2c3d4.png",
    "logoFileName": "company-logo.png",
    "logoUploadTime": "2025-01-28T21:30:00",
    "defaultLogoUrl": "/t_customer_config/logo/1"
  },
  "timestamp": 1640995200000
}
```

## 权限配置

管理端Logo功能需要以下权限：

- `t:customer:config:logo:upload` - 上传Logo权限
- `t:customer:config:logo:delete` - 删除Logo权限  
- `t:customer:config:logo:info` - 查看Logo信息权限

## 数据库变更

执行以下SQL语句更新数据库结构：

```sql
-- 扩展t_customer_config表，添加logo相关字段
ALTER TABLE t_customer_config 
ADD COLUMN logo_url VARCHAR(500) DEFAULT NULL COMMENT '客户自定义logo地址',
ADD COLUMN logo_file_name VARCHAR(200) DEFAULT NULL COMMENT 'logo文件名',
ADD COLUMN logo_upload_time DATETIME DEFAULT NULL COMMENT 'logo上传时间';

-- 添加索引
CREATE INDEX idx_customer_config_logo ON t_customer_config(logo_url);
```

## 文件存储结构

```
ljwx-boot/uploads/
├── logos/
│   ├── customer_{customerId}/           # 各客户的Logo目录
│   │   └── logo_{timestamp}_{uuid}.{ext} # 实际Logo文件
│   └── defaults/                       # 默认Logo目录
│       └── default-logo.svg           # 系统默认Logo
└── .gitkeep                           # 保持目录结构
```

## 访问示例

1. **前端显示Logo**:
```javascript
// 获取客户Logo信息
const logoInfo = await fetch(`/customer/logo/info/${customerId}`);

// 直接使用统一接口显示Logo
<img src={`/customer/logo/${customerId}`} alt="客户Logo" />
```

2. **管理界面上传Logo**:
```html
<form enctype="multipart/form-data">
  <input type="file" name="file" accept="image/*" />
  <input type="hidden" name="customerId" value="1" />
  <button type="submit">上传Logo</button>
</form>
```

## 特性说明

1. **多租户支持**: 每个客户(customerId)可以有独立的Logo
2. **自动降级**: 如果客户没有自定义Logo，自动返回系统默认Logo
3. **文件管理**: 上传新Logo时会自动删除旧Logo文件
4. **缓存优化**: Logo文件设置1天缓存时间，提高访问性能
5. **安全验证**: 支持文件格式和大小验证，防止恶意上传
6. **统一接口**: `/customer/logo/{customerId}` 统一入口，简化前端调用

## 错误代码

| 错误代码 | 说明 |
|---------|-----|
| 400 | 客户不存在、文件格式不支持、文件过大等 |
| 404 | Logo文件不存在（理论上不会发生，因为有默认Logo） |
| 500 | 服务器内部错误 |

## 注意事项

1. 上传Logo前建议先调用信息查询接口确认客户存在
2. 删除Logo操作不可撤销，建议添加二次确认
3. Logo文件建议尺寸为 200x60px 以获得最佳显示效果
4. SVG格式Logo在不同浏览器中可能存在兼容性差异