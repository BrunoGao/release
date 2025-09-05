# BigScreen 弹出框交互问题修复方案

## 问题描述

在 `ljwx-bigscreen` 系统的大屏界面中，存在弹出框交互逻辑错误：

**问题现象**：
1. 点击告警点弹出告警详情框
2. 点击告警框中的"健康数据详情"链接，弹出健康信息详情框
3. **问题**：关闭健康信息详情框时，告警详情框也被意外关闭，而不是返回到告警详情框

**期望行为**：
关闭健康信息详情框应该返回到告警详情框，而不是完全关闭所有弹出框。

## 问题根因分析

通过详细的日志追踪和调试，发现了以下问题：

### 1. 函数调用链问题

**`showCustomMapInfo()` 函数**（显示告警弹出框）：
- 调用 `removeCustomMapInfo()` 清理所有现有面板
- 这个函数会移除地图信息面板和健康详情面板

**`showHealthProfile()` 函数**（显示健康详情弹出框）：
- 也调用 `removeCustomMapInfo()` 清理所有现有面板
- 导致告警弹出框被意外清除

### 2. 事件冒泡问题

健康详情弹出框的关闭按钮点击事件会冒泡到地图，触发地图点击事件：
- 地图点击事件检测到没有特征点时调用 `removeCustomMapInfo()`
- 导致所有面板被清除

### 3. 状态管理问题

全局 `panelDisplaying` 状态管理存在问题：
- `showCustomMapInfo` 显示后设置 `panelDisplaying = true`
- 通过300ms延时重置为 `false`
- 在延时期间用户点击健康详情会被错误阻止

## 解决方案

### 1. 修复面板清理逻辑

**修改前**：
```javascript
// showCustomMapInfo 中
removeCustomMapInfo(); // 清理所有面板

// showHealthProfile 中  
removeCustomMapInfo(); // 清理所有面板
```

**修改后**：
```javascript
// showCustomMapInfo - 精确清理
const existingMapInfo = document.querySelector('.custom-map-info');
if(existingMapInfo) existingMapInfo.remove();
const existingHealthModal = document.querySelector('.health-modal-overlay');
if(existingHealthModal) existingHealthModal.remove();

// showHealthProfile - 只清理健康详情面板，保留告警弹出框
const existingHealthModal = document.querySelector('.health-modal-overlay');
if(existingHealthModal) existingHealthModal.remove();
```

### 2. 创建专用关闭函数

新增 `closeHealthModal()` 函数专门处理健康详情面板关闭：

```javascript
function closeHealthModal(event){
  // 阻止事件冒泡，防止触发地图点击事件
  if(event && event.stopPropagation){
    event.stopPropagation();
    event.preventDefault();
  }
  
  // 只移除健康详情面板，不影响告警弹出框
  const healthModal = document.querySelector('.health-modal-overlay');
  if(healthModal){
    healthModal.remove();
    console.log('健康详情面板已关闭，重置显示状态');
  }
  
  panelDisplaying = false;
}
```

### 3. 优化状态管理逻辑

**修改前**：
```javascript
// 使用全局 panelDisplaying 状态防抖
if(panelDisplaying) {
  console.log('面板正在显示中，跳过重复调用');
  return;
}
```

**修改后**：
```javascript
// showCustomMapInfo - 检查具体面板
const existingMapInfo = document.querySelector('.custom-map-info');
if(existingMapInfo) {
  console.log('地图信息面板已存在，跳过重复调用');
  return;
}

// showHealthProfile - 检查具体面板
const existingHealthModal = document.querySelector('.health-modal-overlay');
if(existingHealthModal) {
  console.log('健康详情面板已存在，跳过重复调用');
  return;
}
```

### 4. 添加事件阻止冒泡

为健康详情弹出框添加完整的事件处理：

```javascript
// 内容区域点击阻止冒泡
const healthContent = m.querySelector('.health-modal-content');
if(healthContent){
  healthContent.addEventListener('click', function(e) {
    console.log('健康详情内容区域被点击，阻止冒泡');
    e.stopPropagation();
  });
}

// 遮罩层点击关闭
m.addEventListener('click', function(e) {
  if(e.target === m){
    console.log('点击遮罩层，关闭健康详情面板');
    e.stopPropagation();
    e.preventDefault();
    closeHealthModal();
  }
});
```

## 修改文件

**主要修改文件**：
- `ljwx-bigscreen/bigscreen/bigScreen/templates/bigscreen_main.html`

**修改行数**：
- 6814行：健康详情关闭按钮调用函数
- 6077-6083行：`showCustomMapInfo` 面板清理逻辑
- 6620-6625行：`showHealthProfile` 面板清理逻辑
- 7022-7036行：新增 `closeHealthModal` 函数
- 6996-7021行：健康详情弹出框事件处理

## 测试验证

修复后的交互流程：

1. ✅ 点击告警点 → 显示告警弹出框
2. ✅ 点击"健康数据详情" → 显示健康信息弹出框（告警框保留）
3. ✅ 关闭健康信息弹出框 → 返回到告警弹出框（符合预期）
4. ✅ 关闭告警弹出框 → 完全关闭所有弹出框

## 技术要点总结

1. **精确的面板管理**：不使用全局清理函数，而是精确管理每个面板的显示和隐藏
2. **事件冒泡控制**：正确使用 `stopPropagation()` 防止事件冒泡导致的意外行为
3. **状态管理优化**：使用具体的DOM查询代替全局状态标志，避免时序问题
4. **专用处理函数**：为不同类型的弹出框创建专用的处理函数，避免逻辑混乱

## 修复完成时间

2025-01-27

## 影响范围

- 修复范围：BigScreen 告警点弹出框和健康详情弹出框的交互逻辑
- 兼容性：完全向后兼容，不影响其他功能
- 风险评估：低风险，仅优化弹出框交互逻辑