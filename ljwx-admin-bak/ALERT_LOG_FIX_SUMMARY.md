# 告警日志表格修复总结

## 问题分析

### 1. 全选问题
**原因**：NDataTable的`:row-key`配置错误
- **错误配置**：`:row-key="row => row.id"`
- **正确配置**：`:row-key="row => row.logId"`
- **说明**：数据库主键是`log_id`，对应的实体字段是`logId`，而不是基类的`id`字段

### 2. 删除失败问题
**原因**：删除操作使用了错误的字段
- **错误**：`handleDelete(row.id)` - id字段为0或未定义
- **正确**：`handleDelete(row.logId)` - 使用实际的主键logId
- **影响**：导致传递ids=[0]给后端删除接口

## 技术细节

### 数据库表结构
```sql
-- t_alert_action_log 表
log_id BIGINT PRIMARY KEY AUTO_INCREMENT  -- 主键
id INTEGER                                 -- 普通字段(可为空)
alert_id BIGINT                           -- 告警ID
-- ... 其他字段
```

### Java实体映射
```java
@TableName("t_alert_action_log")
public class TAlertActionLog extends BaseEntity {
    private Long logId;  // 对应 log_id (主键)
    // BaseEntity.id 对应普通的 id 字段
}
```

### MyBatis映射配置
```xml
<resultMap id="TAlertActionLogResultMap">
    <id column="log_id" property="logId" />  <!-- 主键映射 -->
    <!-- 其他字段映射 -->
</resultMap>
```

## 修复方案

### 1. 修复表格row-key配置
```vue
<NDataTable
  :row-key="row => row.logId"  <!-- 使用logId作为row-key -->
  v-model:checked-row-keys="checkedRowKeys"
  <!-- 其他配置 -->
/>
```

### 2. 修复删除操作
```vue
<!-- 删除按钮 -->
<NPopconfirm onPositiveClick={() => handleDelete(row.logId)}>
  <!-- 使用logId而不是id -->
</NPopconfirm>
```

```typescript
async function handleDelete(id: number) {  // 参数类型为number
  const { error, data: result } = await fetchDeleteAleractionLog(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}
```

### 3. 修复批量删除
确保`checkedRowKeys`中收集的是`logId`值，而不是`id`值。

## 验证方法

### 1. 测试单选
- 点击单个复选框，不应该触发全选
- 检查控制台`checkedRowKeys`数组内容

### 2. 测试删除
- 单个删除：检查发送的ID是否为正确的logId
- 批量删除：检查发送的IDs数组内容

### 3. API调试
```bash
# 正确的删除请求应该是：
POST /t_alert_action_log/
{
  "ids": [12, 11, 10]  # 实际的logId值
}

# 而不是：
{
  "ids": [0]  # 错误的id值
}
```

## 注意事项

1. **字段命名一致性**：确保前端、后端、数据库字段映射一致
2. **类型安全**：logId是number类型，确保类型匹配
3. **测试覆盖**：测试单选、多选、全选、删除等完整流程

## 相关文件

- `ljwx-admin/src/views/alert/log/index.vue` - 主页面
- `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/domain/entity/TAlertActionLog.java` - 实体类
- `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/repository/mapper/TAlertActionLogMapper.xml` - 映射文件
