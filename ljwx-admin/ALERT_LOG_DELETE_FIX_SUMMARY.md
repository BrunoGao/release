# 告警日志删除功能修复完整总结

## 🔍 **问题诊断**

### 1. 前端表格问题
- **全选异常**：点击单个复选框触发全选
- **删除失败**：传递错误的ID值 `[0]` 而不是实际的 `logId`

### 2. 后端删除问题
- **实体类主键配置错误**：MyBatis-Plus无法识别正确的主键字段
- **数据库操作失败**：删除操作实际没有执行

## ⚠️ **根本原因分析**

### 数据库表结构
```sql
-- t_alert_action_log 表结构
CREATE TABLE t_alert_action_log (
  log_id BIGINT PRIMARY KEY AUTO_INCREMENT,  -- 实际主键
  id INTEGER,                                 -- 普通字段(可为NULL)
  alert_id BIGINT,
  -- ... 其他字段
);
```

### 问题核心
1. **前端**: `:row-key="row => row.id"` 使用了错误的字段（值为NULL）
2. **后端**: TAlertActionLog实体类继承BaseEntity，MyBatis-Plus默认使用BaseEntity.id作为主键
3. **映射错误**: 实际主键`log_id`没有被正确标识为@TableId

## 🔧 **完整修复方案**

### 1. 前端修复 (ljwx-admin)

**文件**: `ljwx-admin/src/views/alert/log/index.vue`

```vue
<!-- 修复表格row-key -->
<NDataTable
  :row-key="row => row.logId"  <!-- ✅ 使用logId -->
  v-model:checked-row-keys="checkedRowKeys"
  <!-- 其他配置 -->
/>

<!-- 修复删除操作 -->
<NPopconfirm onPositiveClick={() => handleDelete(row.logId)}>
  <!-- ✅ 使用logId而不是id -->
</NPopconfirm>
```

```typescript
// 修复函数参数类型
async function handleDelete(id: number) {  // ✅ number类型
  const { error, data: result } = await fetchDeleteAleractionLog(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}
```

### 2. 后端修复 (ljwx-boot)

**文件**: `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/domain/entity/TAlertActionLog.java`

```java
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_alert_action_log")
public class TAlertActionLog extends BaseEntity {

    // ✅ 排除BaseEntity的id字段，避免@TableId冲突
    @TableField(exist = false)
    private Long id;

    @TableId // ✅ 指定logId为主键
    private Long logId;

    // ... 其他字段
}
```

### 3. 重新编译和部署

```bash
# 1. 重新编译modules项目
mvn clean install -DskipTests -pl ljwx-boot-modules

# 2. 使用正确的启动方式
cd ljwx-boot
./run-local.sh  # ✅ 正确的启动脚本，而不是在ljwx-boot-admin目录下执行
```

## ✅ **验证方法**

### 1. 前端验证
- **单选测试**: 点击单个复选框，不应触发全选
- **删除测试**: 检查Network面板，确认传递正确的logId值

### 2. 后端验证
```bash
# 查看后端日志，应该看到正确的ID
curl -X DELETE "http://localhost:3333/proxy-default/t_alert_action_log/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"ids":[12]}'

# 后端日志应显示：
# setNonNullParameter called with parameter: ["{\"ids\":[12]}"]
```

### 3. 数据库验证
```sql
-- 删除前
SELECT log_id FROM t_alert_action_log WHERE log_id = 12;  -- 应该存在

-- 删除后
SELECT log_id FROM t_alert_action_log WHERE log_id = 12;  -- 应该为空
```

## 🎯 **技术要点总结**

### MyBatis-Plus主键配置规则
1. **默认主键**: 如果没有@TableId注解，使用BaseEntity.id
2. **自定义主键**: 使用@TableId明确指定主键字段
3. **冲突解决**: 当继承BaseEntity时，需要排除BaseEntity.id字段

### 前端表格配置
1. **row-key**: 必须使用实际的主键字段
2. **类型安全**: 确保ID类型匹配（number vs string）
3. **删除操作**: 使用正确的字段名称

## 📝 **相关文件清单**

### 前端修改
- `ljwx-admin/src/views/alert/log/index.vue`
- `ljwx-admin/ALERT_LOG_FIX_SUMMARY.md`

### 后端修改
- `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/domain/entity/TAlertActionLog.java`

### 启动方式修正
- ❌ `cd ljwx-boot-admin && mvn spring-boot:run`
- ✅ `cd ljwx-boot && ./run-local.sh`

## 🎉 **修复状态**

- ✅ **前端全选问题**: 已修复
- ✅ **前端删除ID传递**: 已修复
- ✅ **后端实体类主键配置**: 已修复
- ✅ **启动方式**: 已修正
- 🔄 **整体测试**: 待用户验证

现在所有修复都已完成，用户可以正常使用告警日志的单选、删除等功能了！
