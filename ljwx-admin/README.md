# LjwxAdmin 后台管理系统

![Node](https://img.shields.io/badge/Node-18-blue.svg)
![Version](https://img.shields.io/badge/Version-1.3.4-blue.svg)
[![License](https://img.shields.io/badge/License-Apache%20License%202.0-B9D6AF.svg)](./LICENSE)
<br/>
[![Author](https://img.shields.io/badge/Author-paynezhuang-green.svg)](https://github.com/paynezhuang)
[![Copyright](https://img.shields.io/badge/Copyright-2024%20Zhuang%20Pan%20@LjwxAdmin-green.svg)](https://github.com/paynezhuang)

### 项目简介


[`LingjingAdmin`](https://github.com/BrunoGao/platform) 基于 [`SoybeanAdmin`](https://github.com/soybeanjs/soybean-admin) 二次修改而来。它是一个清新优雅、高颜值且功能强大的后台管理模板，采用`Naive UI`组件库，并最新的前端技术栈，包括 Vue3, Vite5, TypeScript, Pinia 和 UnoCSS。它内置了丰富的主题配置和组件，代码规范严谨，实现了自动化的文件路由系统。`LingjingAdmin` 为您提供了一站式的后台管理解决方案，无需额外配置，开箱即用。同样是一个快速学习前沿技术的最佳实践。

在此特别感谢开源作者：[Soybean](https://github.com/honghuangdc) 。

### 项目特性

- **前沿技术应用**：采用 Vue3, Vite5, TypeScript, Pinia 和 UnoCSS 等最新流行的技术栈。
- **清晰的项目架构**：采用 pnpm monorepo 架构，结构清晰，优雅易懂。
- **严格的代码规范**：遵循 [SoybeanJS 规范](https://docs.soybeanjs.cn/zh/standard)，集成了eslint, prettier 和 simple-git-hooks，保证代码的规范性。
- **TypeScript**： 支持严格的类型检查，提高代码的可维护性。
- **丰富的主题配置**：内置多样的主题配置，与 UnoCSS 完美结合。
- **内置国际化方案**：轻松实现多语言支持。
- **自动化文件路由系统**：自动生成路由导入、声明和类型。更多细节请查看 [Elegant Router](https://github.com/soybeanjs/elegant-router)。
- **灵活的权限路由**：同时支持前端静态路由和后端动态路由。
- **丰富的页面组件**：内置多样页面和组件，包括403、404、500页面，以及布局组件、标签组件、主题配置组件等。
- **命令行工具**：内置高效的命令行工具，git提交、删除文件、发布等。
- **移动端适配**：完美支持移动端，实现自适应布局。

### 项目源码

| 名称      | 链接                                                                      |
|:--------|:------------------------------------------------------------------------|
| 前端      | [Lingjing-admin](https://github.com/BrunoGao/platform)               |
| 后端      | [Lingjing-boot](https://github.com/BrunoGao/platform)                 |
| 后端扩展依赖库 | [Lingjing-boot-starter](https://github.com/BrunoGao/platform) |

### 项目启动

##### 前置环境

- **Git**: 你需要git来克隆和管理项目版本。
- **NodeJS**: >=18.12.0，推荐 18.19.0 或更高。
- **pnpm**: >= 8.7.0，推荐 8.14.0 或更高。

##### 克隆项目

```bash
git clone https://github.com/BrunoGao/platform.git
```

##### 项目启动

1. 安装依赖
```bash
pnpm i
```
> 由于本项目采用了 pnpm monorepo 的管理方式，因此请不要使用 npm 或 yarn 来安装依赖。

2. 启动项目，修改`.env.test`中`VITE_SERVICE_BASE_URL`对应的后端地址
```bash
pnpm dev
```

##### 构建项目

修改`.env.prod`中`VITE_SERVICE_BASE_URL`对应的后端地址

```bash
pnpm build
```

### Git 提交规范

本项目已内置 `commit` 命令，您可以通过执行 `pnpm commit` 来生成符合 [Conventional Commits]([conventionalcommits](https://www.conventionalcommits.org/)) 规范的提交信息。在提交PR时，请务必使用 `commit` 命令来创建提交信息，以确保信息的规范性。


### 示例图片

![](./doc/images/Login.png)

| ![Home](./doc/images/Home.png) | ![Home-2](./doc/images/Home-2.png) |
|--------------------------------|--------------------------------|
| ![User](./doc/images/User.png) | ![User-2](./doc/images/User-2.png) |
| ![Role](./doc/images/Role-Permission.png) | ![Role](./doc/images/Role-Menu.png) |
| ![Menu](./doc/images/Menu.png) | ![Menu-2](./doc/images/Menu-2.png) |
| ![Menu-3](./doc/images/Menu-3.png) |![User-Dark](./doc/images/User-Dark.png) |
| ![Mobile](./doc/images/Home-Mobile.png) | ![Mobile](./doc/images/User-Mobile.png) |
| ![Mobile](./doc/images/Menu-Mobile.png) | ![Mobile](./doc/images/Menu-Mobile-Dark.png)|

### 浏览器支持

推荐使用最新版的 Chrome 浏览器进行开发，以获得更好的体验。

| [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/archive/internet-explorer_9-11/internet-explorer_9-11_48x48.png" alt="IE" width="24px" height="24px"  />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/edge/edge_48x48.png" alt=" Edge" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/firefox/firefox_48x48.png" alt="Firefox" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/chrome/chrome_48x48.png" alt="Chrome" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/safari/safari_48x48.png" alt="Safari" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) |
| --- | --- | --- | --- | --- |
| not support | last 2 versions | last 2 versions | last 2 versions | last 2 versions |

### 特别鸣谢

- [SoybeanJS](https://github.com/soybeanjs)
- [Naive UI](https://www.naiveui.com/zh-CN/os-theme)
- [Vue](https://cn.vuejs.org/)
- 不一一列举，感谢所有开源项目的贡献者

### 开源协议

项目基于 [Apache License 2.0 © 2024 ljwx](./LICENSE) 协议，仅供学习参考，商业使用请遵循作者版权信息，作者不保证也不承担任何软件的使用风险。

## 功能说明

### 员工列表初始化
- 页面初始化时会根据部门自动拉取员工列表
- 部门变更时会自动更新员工列表
- 支持模糊搜索员工

### 表单验证优化 (最新)

#### 功能概述
- 优化员工新增/编辑表单的实时验证体验
- 员工名字和手机号格式错误时，修正后自动清除验证提示
- 无需关闭抽屉重新打开即可清除验证状态

#### 技术实现
- 修改表单验证规则触发器，支持 `input` 和 `change` 双重触发
- 优化 `userName` 和 `phone` 字段的验证响应机制
- 修复 `UserEdit` 类型定义，移除不必要的字段

#### 使用体验
1. **输入验证**：用户输入时立即显示格式错误提示
2. **实时清除**：修正输入后验证错误自动消失
3. **无缝操作**：提升表单操作的流畅性和用户体验

### 告警时序统计图
- 主页面饼图已替换为告警时序统计图
- 使用真实告警数据，自动根据数据实际时间范围生成时序图
- 支持中文显示：心率、血压、体温等告警类型，待处理、已响应、已解决等状态
- 按照alertType（折线图）、severityLevel（柱状图）维度分组展示
- 智能时间范围：根据数据跨度自动调整显示7-30天时间窗口
- 时间范围标注：标题显示数据总量和时间跨度（如：1/25-1/25）
- 支持交叉分析和多维度数据对比
- 无数据时显示友好提示信息

### 消息时序统计图
- 新增消息时序分析功能，自动根据数据实际时间范围生成图表
- 支持中文显示：系统消息、告警消息、通知消息等类型，已发送、已送达、已读等状态
- 按照messageType（折线图）、messageStatus（面积图）维度进行时序统计
- 智能时间范围：根据sentTime数据跨度自动调整显示窗口
- 时间范围标注：显示消息总量和时间跨度信息
- 支持多种消息类型的独立统计和状态追踪

### 🔄 用户管理 - 视图模式切换 (最新)

#### 功能概述
- 支持全部用户、员工、管理员三种视图模式切换
- 根据选择的模式动态过滤显示对应用户类型
- 在全部用户视图中显示用户类型标识（管理员/员工）

#### 使用方法
1. 在用户管理页面顶部选择视图模式：
   - **全部用户**：显示所有用户，包含类型标识列
   - **员工**：仅显示普通员工用户
   - **管理员**：仅显示管理员用户

2. 视图模式参数说明：
   ```typescript
   viewMode: 'all' | 'employee' | 'admin'
   ```

3. API调用示例：
   ```typescript
   // 根据视图模式获取用户列表
   fetchGetUserListByViewMode({
     ...params,
     viewMode: 'employee' // 仅获取员工
   })
   ```

#### 技术实现
- 前端组件：`UserViewModeSelector` - 视图模式选择器
- API函数：`fetchGetUserListByViewMode` - 支持viewMode参数
- 类型标识：使用 `NTag` 组件显示用户类型（管理员/员工）

### 👨‍💼 角色管理 - 管理员标识 (最新)

#### 功能概述
- 角色新增/编辑时支持设置是否为管理员角色
- 角色列表显示管理员类型标识
- 与后端数据库 `is_admin` 字段同步

#### 使用方法
1. **新增角色**：
   - 在角色信息表单中选择"普通角色"或"管理员角色"
   - 系统自动将 `isAdmin` 字段设置为 0 或 1

2. **编辑角色**：
   - 可以修改现有角色的管理员属性
   - 保存后立即生效

3. **角色列表**：
   - 显示"是否管理员"列
   - 管理员角色显示为红色标签
   - 普通角色显示为绿色标签

#### 数据库字段
```sql
ALTER TABLE sys_role
ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0
COMMENT '是否为管理员角色（0普通角色，1管理员角色）';
```

#### 技术实现
- 类型定义：`Role.isAdmin: number`
- 表单字段：单选按钮组选择角色类型
- 列表显示：使用 `NTag` 组件显示角色类型标识
- 国际化：支持中英文切换

## 🚀 部署说明

### 开发环境
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 生产环境
```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 📖 API文档

### 用户管理接口

#### 获取用户列表（支持视图模式）
```http
GET /sys_user/page?viewMode={mode}
```

参数：
- `viewMode`: 视图模式 (all/employee/admin)
- 其他分页和搜索参数...

响应：
```json
{
  "code": 200,
  "data": {
    "records": [
      {
        "id": "1",
        "userName": "admin",
        "isAdmin": true,
        "userType": "ADMIN"
      }
    ]
  }
}
```

### 角色管理接口

#### 新增/更新角色
```http
POST/PUT /sys_role/
```

请求体：
```json
{
  "roleName": "系统管理员",
  "roleCode": "ADMIN",
  "isAdmin": 1,
  "status": "1"
}
```

## 🔧 技术栈

- **框架**: Vue 3 + TypeScript
- **UI库**: Naive UI
- **状态管理**: Pinia
- **路由**: Vue Router
- **构建工具**: Vite
- **代码规范**: ESLint + Prettier

### 📥 用户批量导入功能 (最新)

#### 功能概述
- 支持Excel (.xlsx, .xls) 和CSV格式文件批量导入用户
- 智能模板下载，提供标准化的数据格式和字段说明
- 支持部门和岗位的ID或名称两种查询方式
- 详细的导入结果展示，包含成功/失败统计和错误详情

#### 使用方法
1. **下载模板**：
   - 点击"下载导入模板"获取标准CSV模板
   - 模板包含字段：姓名、性别、年龄、工龄、手机号码、部门、岗位、设备序列号、备注
   - 提供完整的示例数据和字段说明

2. **准备数据**：
   - 按模板格式填写用户信息
   - 部门和岗位支持两种输入方式：
     - **ID方式**：直接填写部门/岗位的数字ID（如：11, 1）
     - **名称方式**：填写完整的部门/岗位名称（如：技术部、软件工程师）

3. **上传导入**：
   - 拖拽或点击选择Excel/CSV文件
   - 系统自动验证文件格式和数据完整性
   - 显示详细的导入结果和错误信息

#### 数据验证规则
- **必填字段**：姓名、性别、年龄、工龄、手机号码、部门、岗位
- **格式验证**：
  - 手机号：11位数字，1开头
  - 年龄：0-120范围
  - 工龄：非负数
  - 性别：只能是"男"或"女"
- **唯一性检查**：手机号不能重复
- **权限验证**：只能在授权的组织范围内导入

#### 自动化处理
- **用户名生成**：基于手机号后6位自动生成（格式：user+6位数字）
- **默认密码**：统一设置为"123456"（MD5加密存储）
- **邮箱设置**：自动生成格式为"手机号@example.com"
- **组织关系**：自动建立用户与部门、岗位的关联关系

#### 技术实现
- **文件解析**：集成Apache POI支持Excel解析，自定义CSV解析器
- **数据验证**：多层级验证机制，确保数据完整性和格式正确性
- **权限控制**：基于Sa-Token的导入权限验证和组织数据隔离
- **错误处理**：详细的错误报告和事务回滚机制

### 🚨 告警管理 - 一键批量处理 (最新)

#### 功能概述
- 支持批量选择和处理多条告警记录
- 智能状态检查，自动识别已处理告警并提示用户
- 与 ljwx-bigscreen 服务集成，调用后端批量处理接口
- 详细的操作结果反馈，包含成功/失败数量统计

#### 使用方法
1. **选择告警记录**：
   - 在告警管理页面选择多条（≥2条）告警记录
   - "一键批量处理"按钮将从灰色禁用状态变为可点击的绿色按钮

2. **批量处理操作**：
   - 点击"一键批量处理"按钮
   - 系统自动检查选中告警的状态
   - 如包含已响应告警，会弹出确认对话框供用户选择

3. **操作结果**：
   - 显示详细处理结果：成功X条，失败X条
   - 如有已处理过的告警，会特别标注数量
   - 处理完成后自动刷新列表数据

#### 按钮状态说明
- **默认状态**：灰色禁用，始终显示在批量删除按钮右侧
- **激活条件**：选择2条或更多告警记录时激活
- **禁用条件**：选择少于2条记录或数据加载中时禁用
- **权限控制**：基于 `t:alert:info:update` 权限

#### 技术实现
- **前端组件**：使用 `#suffix` 插槽实现按钮布局
- **状态检查**：检查 `alertStatus === 'responded'` 状态
- **API接口**：调用 ljwx-bigscreen 的 `/batchDealAlert` 接口
- **用户体验**：包含确认对话框、详细反馈信息和权限控制

#### 接口说明
```http
POST http://localhost:5001/batchDealAlert
Content-Type: application/json

{
  "alertIds": ["1", "2", "3"]
}
```

响应格式：
```json
{
  "success": true,
  "message": "批量处理完成：成功2条，失败1条",
  "successCount": 2,
  "failedCount": 1,
  "failedAlerts": [
    {
      "alertId": "3",
      "error": "处理失败"
    }
  ]
}
```

### 🔧 微信告警配置管理 (最新)

#### 功能概述
- 支持企业微信和微信公众号两种类型的告警配置管理
- 动态表格列显示，根据配置类型自适应显示相应字段
- 完整的CRUD操作支持，包含新增、编辑、删除和批量删除功能
- 智能数据过滤和状态管理

#### 功能特点
1. **双类型支持**：
   - **企业微信配置**：显示企业ID、应用ID、应用Secret等企业微信专属字段
   - **微信公众号配置**：显示AppID、AppSecret、微信ID等公众号专属字段

2. **智能表格**：
   - 标签页切换时动态调整表格列
   - 自适应字段显示，避免冗余列
   - 统一的通用字段：模板ID、启用状态、创建时间、操作等

3. **数据管理**：
   - 实时数据同步和状态更新
   - 完整的权限控制和操作验证
   - 敏感信息脱敏显示（Secret字段只显示后4位）

#### 使用方法
1. **查看配置**：
   - 点击"企业微信配置"标签查看企业微信告警配置
   - 点击"微信公众号配置"标签查看公众号告警配置
   - 支持按类型、启用状态等条件搜索过滤

2. **新增配置**：
   - 点击"新增"按钮打开配置表单
   - 根据当前标签页自动设置配置类型
   - 填写对应类型的必要字段信息

3. **编辑配置**：
   - 点击表格中的"编辑"按钮修改配置
   - 支持修改除ID和类型外的所有字段
   - 实时保存并更新表格显示

#### 技术实现
- **动态列定义**：基于 `activeTab` 值动态生成表格列配置
- **状态管理**：使用 Vue 3 的响应式系统实现状态同步
- **API集成**：与后端 `/t_wechat_alarm_config/page` 接口完整对接
- **类型安全**：完整的 TypeScript 类型定义和验证

#### 数据字段映射
```typescript
// 企业微信配置
{
  corpId: string;      // 企业ID
  agentId: string;     // 应用ID
  secret: string;      // 应用Secret
}

// 微信公众号配置
{
  appid: string;       // AppID
  appsecret: string;   // AppSecret
  wechatId: string;    // 微信ID (映射自appid)
}

// 通用字段
{
  templateId: string;  // 模板ID
  enabled: boolean;    // 启用状态
  createTime: string;  // 创建时间
}
```

## 📝 更新日志

### v1.3.6 (2025-08-27)
- 🐛 **修复微信告警配置表格显示空白问题**
  - 解决 NDataTable 的 `remote` 属性与本地数据冲突导致的渲染失败
  - 移除导致问题的属性组合：`remote`、复杂分页配置、动态高度设置
  - 重构列定义为独立 computed 属性，避免 useTable 的 columns 处理丢失 render 函数
  - 修复搜索组件中 `type` 参数传递问题，确保企业微信和微信公众号数据正确过滤
  - 优化操作按钮使用 Vue 的 h 函数，避免 JSX 语法在 Vue 模板中的冲突
- 📚 **新增开发文档**
  - 创建 CLAUDE.md 开发文档，记录数据解析流程和故障排查方法
  - 建立表格渲染问题的快速诊断清单，提升后续开发效率
  - 文档化 NDataTable 使用最佳实践和常见陷阱避免指南

### v1.3.5 (2025-08-27)
- ✨ **新增微信告警配置管理功能**
  - 支持企业微信和微信公众号两种配置类型
  - 动态表格列显示，根据类型自适应字段
  - 完整的CRUD操作和批量管理
  - 敏感信息安全脱敏显示
  - 智能数据过滤和实时状态同步
- 🔧 **修复表格组件显示问题**
  - 解决NDataTable组件数据绑定问题
  - 修复TableHeaderOperation组件导入缺失
  - 优化标签页切换时的数据加载逻辑
  - 完善列定义动态更新机制
- 🐛 **修复数据过滤和状态管理**
  - 修复标签切换时数据不更新的问题
  - 优化searchParams参数传递机制
  - 改进API参数验证和错误处理
  - 增强前后端数据同步稳定性

### v1.3.4 (2025-08-25)
- ✨ **新增健康数据源过滤功能**
  - 健康数据查看时自动过滤通用事件上传的数据
  - 与后端 upload_method 字段联动，过滤掉 "common_event" 类型数据
  - 确保健康信息页面仅显示正常健康监测数据，提高数据准确性
  - 优化数据展示逻辑，提升用户查看健康报告的体验

### v1.3.3 (2025-08-20)
- ✨ **新增用户批量导入功能**
  - 支持Excel (.xlsx, .xls) 和CSV格式文件导入
  - 智能模板下载，包含完整字段示例和说明
  - 支持部门和岗位的ID/名称双重查询方式
  - 实时文件验证和格式检查
  - 详细的导入结果展示和错误反馈
  - 现代化的拖拽上传界面
  - 完整的权限控制和数据隔离
- 🔧 **文件上传组件优化**
  - 替换NUpload组件为原生HTML文件输入
  - 修复FormData文件传输问题
  - 添加直接fetch上传备用方案
  - 优化文件选择和验证流程
- 🛡️ **数据安全增强**
  - 严格的文件类型验证
  - 多层级数据校验机制
  - 按组织架构的权限隔离
  - 完整的错误处理和事务回滚

### v1.2.17 (2025-01-14)
- ✨ **新增告警管理一键批量处理功能**
  - 支持多选告警记录进行批量处理操作
  - 智能状态检查，已响应告警会弹出确认提示
  - 详细的处理结果反馈，包含成功/失败统计信息
  - 按钮默认灰色禁用，多选时激活，位于批量删除右侧
  - 集成 ljwx-bigscreen 后端服务，调用 /batchDealAlert 接口
  - 完整的权限控制和用户体验优化

### v1.2.16 (2024-12-18)
- 🐛 **修复员工表单验证体验问题**
  - 修复员工名字格式错误修正后需关闭抽屉才能清除验证提示的问题
  - 优化表单验证触发机制，支持实时清除验证状态
  - 改进用户名和手机号字段的验证响应，提升操作流畅性
  - 修复UserEdit类型定义，确保类型安全
- 🔧 优化表单验证规则，支持input和change双重触发模式

### v1.2.15 (2024-12-18)
- ✨ 新增用户管理视图模式切换功能
- ✨ 新增角色管理员标识字段
- 🔧 优化用户类型显示和过滤
- 🌐 完善中英文国际化配置
- 🐛 修复viewMode参数传递问题

### v1.2.14
- 🔧 基础功能完善
- 📱 响应式界面优化

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情
