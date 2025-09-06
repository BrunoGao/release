# LjwxAdmin Claude 开发文档

## 数据解析与表格渲染故障排查文档

### 概述
本文档详细记录了 LjwxAdmin 项目中 API 数据解析流程和表格渲染机制，以及一次耗时的微信告警配置表格显示故障的完整排查过程。

### 核心数据流架构

#### 1. API 调用层
```typescript
// src/service/api/health/alert-config-wechat.ts
export function fetchGetAlertConfigWechatList(params?: Api.Health.AlertConfigWechatSearchParams) {
  return request<Api.Health.AlertConfigWechatList>({
    url: '/t_wechat_alarm_config/page',
    method: 'GET',
    params
  });
}
```

#### 2. useTable Hook 数据转换层
```typescript
// src/hooks/common/table.ts
const { loading, data, columns, getData, searchParams } = useTable({
  apiFn: fetchGetAlertConfigWechatList,
  apiParams: { page: 1, pageSize: 20, customerId, type: 'enterprise' },
  transformer: res => {
    const { records = [], page = 1, pageSize = 20, total = 0 } = res.data || {};
    const recordsWithIndex = records.map((item, index) => ({
      ...item,
      index: (page - 1) * pageSize + index + 1
    }));
    return { data: recordsWithIndex, pageNum: page, pageSize, total };
  },
  columns: () => { /* 动态列定义 */ }
});
```

#### 3. Vue 组件渲染层
```vue
<NDataTable
  :data="data"
  :columns="columns"
  :row-key="(row) => row.id"
/>
```

### 数据流详细分析

#### API 响应格式
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "page": 1,
    "pageSize": 20,
    "total": 2,
    "records": [
      {
        "id": 10,
        "type": "official",
        "appid": "wx10dcc9f0235e1d77",
        "templateId": "xxx",
        "enabled": true,
        "createTime": 1750168835000
      }
    ]
  }
}
```

#### transformer 转换过程
1. **提取分页数据**：从 `res.data` 中解构 `records`, `page`, `pageSize`, `total`
2. **添加索引**：为每条记录添加 `index` 字段，用于表格序号显示
3. **返回标准格式**：返回 `{ data, pageNum, pageSize, total }` 供 useTable 使用

#### 列定义处理
useTable hook 通过 `getColumns` 函数处理列定义：
```typescript
getColumns: (cols, checks) => {
  const columnMap = new Map();
  cols.forEach(column => {
    if (isTableColumnHasKey(column)) {
      columnMap.set(column.key, column);
    }
  });
  return checks.filter(item => item.checked).map(check => columnMap.get(check.key));
}
```

### 故障案例：微信告警配置表格显示空白

#### 问题现象
- API 正常返回数据
- data 数组长度正确
- columns 数组长度正确
- 但 NDataTable 表格完全空白

#### 排查过程

##### 第一阶段：参数传递问题
**怀疑**：API 参数传递错误
**排查**：
```typescript
// 修复搜索组件 type 参数传递
watch(() => props.type, (newType) => {
  if (newType) {
    model.value.type = newType;
  }
}, { immediate: true });
```
**结果**：API 能正确返回数据，但表格仍空白

##### 第二阶段：数据过滤问题
**怀疑**：前端数据过滤导致显示为空
**排查**：
```typescript
// 添加 filteredData 计算属性
const filteredData = computed(() => {
  if (!data.value) return [];
  return data.value.filter(item => item.type === activeTab.value);
});
```
**结果**：数据过滤正确，但表格仍空白

##### 第三阶段：useTable hook 问题
**怀疑**：useTable 的 columns 处理丢失了 render 函数
**排查**：
```json
// 调试发现列定义中缺失 render 函数
[
  { "key": "corpId", "title": "企业ID", "align": "center", "width": 150 },
  // render 函数在 JSON.stringify 时丢失了！
]
```
**发现**：useTable 的 getColumns 函数在处理列定义时，render 函数被丢失

##### 第四阶段：NDataTable 属性问题
**怀疑**：NDataTable 的某些属性导致渲染失败
**排查**：逐个移除属性测试
```typescript
// 问题属性组合
<NDataTable
  remote              // ❌ 导致问题的关键属性
  :pagination="mobilePagination"  // ❌ 分页配置问题
  :flex-height="!appStore.isMobile"  // ❌ 高度配置问题
  class="sm:h-full"   // ❌ CSS 类冲突
  :data="data"
  :columns="columns"
/>

// 修复后的简化版本
<NDataTable
  :data="data"
  :columns="columns"
  :row-key="(row) => row.id"
  size="small"
  striped
  :loading="loading"
/>
```

#### 根本原因
1. **`remote` 属性**：告诉 NDataTable 期待远程分页，但我们提供的是本地数据
2. **复杂的分页配置**：mobilePagination 与数据状态不匹配
3. **CSS 高度问题**：flex-height 和相关 CSS 类导致表格高度为 0

### 故障排查最佳实践

#### 1. 分层排查法
```
数据层 → 转换层 → 组件层 → 渲染层
  ↓        ↓       ↓       ↓
 API    useTable  Vue组件  DOM
```

#### 2. 调试工具使用
```typescript
// 在关键节点添加调试输出
console.log('[API] 原始响应:', response);
console.log('[Transformer] 转换后数据:', transformedData);
console.log('[Component] 渲染数据:', data.value);
console.log('[Columns] 列定义:', columns.value);
```

#### 3. 对比测试法
```vue
<!-- 使用简化的测试表格对比 -->
<NDataTable
  :data="data"
  :columns="[
    { key: 'id', title: 'ID' },
    { key: 'type', title: '类型' }
  ]"
  :row-key="(row) => row.id"
/>
```

### NDataTable 使用指南

#### ✅ 推荐配置
```vue
<NDataTable
  :data="data"
  :columns="columns"
  :row-key="(row) => row.id"
  size="small"
  striped
  :loading="loading"
  v-model:checked-row-keys="checkedRowKeys"
/>
```

#### ❌ 避免的属性组合
```vue
<NDataTable
  remote              <!-- 除非真正需要远程分页 -->
  :pagination="complexPagination"  <!-- 避免复杂分页配置 -->
  :flex-height="dynamicValue"      <!-- 避免动态高度计算 -->
  class="complex-css-classes"      <!-- 避免可能冲突的CSS类 -->
/>
```

#### 列定义最佳实践
```typescript
// ✅ 使用 computed 属性，不依赖 useTable 的 columns
const tableColumns = computed(() => [
  { key: 'id', title: 'ID', width: 80 },
  { 
    key: 'status', 
    title: '状态', 
    render: (row) => row.enabled ? '启用' : '禁用' 
  },
  {
    key: 'operate',
    title: '操作',
    render: (row) => h(NButton, { onClick: () => edit(row) }, () => '编辑')
  }
]);

// ❌ 避免依赖 useTable 的动态列定义处理
```

### 类似问题快速诊断清单

#### 1. 数据检查 (30秒)
- [ ] API 是否返回正确数据？
- [ ] `data.length > 0` 是否为真？
- [ ] 数据结构是否与列定义匹配？

#### 2. 列定义检查 (1分钟)
- [ ] `columns.length > 0` 是否为真？
- [ ] render 函数是否丢失？
- [ ] key 字段是否与数据字段匹配？

#### 3. 组件属性检查 (2分钟)
- [ ] 移除 `remote` 属性测试
- [ ] 移除 `pagination` 属性测试
- [ ] 使用最简化的 NDataTable 配置测试

#### 4. 对比测试 (2分钟)
- [ ] 创建简化版本的测试表格
- [ ] 使用相同数据和简单列定义
- [ ] 确认是数据问题还是组件问题

### 总结

这次故障排查耗时的主要原因：
1. **问题隐蔽性**：表面现象（表格空白）与根本原因（NDataTable属性配置）没有直接关联
2. **多层抽象**：useTable hook 增加了调试复杂度
3. **属性依赖**：多个 NDataTable 属性的组合效应难以预测

通过建立这套分层排查方法和文档化的最佳实践，类似问题的排查时间可以从数小时缩短到数分钟。

## 多租户 CustomerId 自动注入功能

### 功能概述
为了更好地支持多租户架构，在前端 ljwx-admin 中实现了全局自动注入 `customerId` 的功能。该功能在请求拦截器层面统一处理，无需在每个 API 调用中手动添加 `customerId` 参数。

### 实现原理
在 `src/service/request/index.ts` 的 `onRequest` 拦截器中实现：

1. **自动检测**：检查当前用户的 `customerId` 是否存在
2. **白名单过滤**：排除不需要 `customerId` 的特殊 API（如认证、字典等）
3. **智能注入**：
   - GET 请求：添加到 `params` 查询参数
   - POST/PUT/DELETE 请求：添加到 `data` 请求体
   - FormData 请求：作为表单字段添加
4. **防重复**：只有当请求中没有显式传入 `customerId` 时才自动添加

### 白名单配置
```typescript
const EXCLUDE_CUSTOMER_ID_URLS = [
  '/auth/',           // 认证相关
  '/login',           // 登录
  '/refresh',         // 刷新token
  '/sys/dict',        // 字典数据(全局)
  '/captcha',         // 验证码
  '/logout'           // 登出
];
```

### 使用示例

#### 原来需要手动添加
```typescript
// 旧方式：每个API调用都要手动添加 customerId
fetchGetUserList({
  page: 1,
  pageSize: 20,
  customerId: authStore.userInfo.customerId
});
```

#### 现在自动注入
```typescript
// 新方式：系统自动注入，无需手动添加
fetchGetUserList({
  page: 1,
  pageSize: 20
  // customerId 会被自动添加
});
```

### 特殊情况处理

#### 1. 显式传入 customerId
```typescript
// 显式传入的值会被保留，不会被自动注入覆盖
fetchGetUserList({
  page: 1,
  pageSize: 20,
  customerId: 999  // 使用这个值，不会被自动注入覆盖
});
```

#### 2. 超级管理员（customerId = 0）
```typescript
// customerId = 0 的超级管理员也会正常注入参数
// 后端可以根据 customerId = 0 判断是否返回全局数据
```

#### 3. FormData 类型请求
```typescript
// 文件上传等 FormData 请求也会自动添加 customerId
const formData = new FormData();
formData.append('file', file);
// 系统自动添加: formData.append('customerId', userInfo.customerId);
```

### 技术优势

1. **零侵入**：不需要修改现有 70+ 个文件的 API 调用代码
2. **向后兼容**：已有的 `customerId` 参数不会被覆盖
3. **统一管理**：在一个地方控制所有 API 的多租户行为
4. **灵活配置**：通过白名单机制精确控制哪些 API 需要自动注入
5. **类型安全**：TypeScript 完全支持，不需要修改类型定义

### 调试方法
如需调试，可在 `onRequest` 拦截器中添加 console.log：
```typescript
if (shouldAddCustomerId) {
  const customerId = authStore.userInfo.customerId;
  console.log(`[CustomerId Auto-Injection] URL: ${config.url}, Method: ${config.method}, CustomerId: ${customerId}`);
  // ... 注入逻辑
}
```

---

## 项目开发注意事项

### 1. 表格开发规范
- 避免使用 `remote` 属性，除非确实需要远程分页
- 列定义使用独立的 computed 属性，不依赖 useTable 的 columns 处理
- 优先使用简化的 NDataTable 配置，渐进式添加复杂功能

### 2. 调试技巧
- 数据问题时，先用简化测试表格验证数据正确性
- 使用分层排查法，从 API → useTable → 组件 → 渲染逐层检查
- 重要的调试信息要保留在代码注释中

### 3. 常见陷阱
- useTable hook 的 transformer 会自动添加 index 字段
- NDataTable 的 render 函数在 JSON.stringify 时会丢失
- type 参数需要在搜索组件中正确设置和传递